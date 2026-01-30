import google.generativeai as genai
from PIL import Image
import io
import re
from typing import Tuple, Optional
from app.config import settings

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)


def extract_food_weight_from_image(image_bytes: bytes) -> Tuple[Optional[float], str, str]:
    """
    Extract food weight from kitchen scale image using Gemini Vision.

    Args:
        image_bytes: Image bytes of kitchen scale

    Returns:
        Tuple of (weight_grams, confidence, message)
        - weight_grams: Extracted weight in grams or None if extraction failed
        - confidence: "high", "medium", or "low"
        - message: Additional information or error message
    """
    try:
        # Load image
        image = Image.open(io.BytesIO(image_bytes))

        # Use Gemini Vision model
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """
        You are analyzing an image of a kitchen scale showing food weight.

        Instructions:
        1. Look for the numeric weight displayed on the scale
        2. Extract ONLY the weight number (ignore tare, unit labels, etc.)
        3. Convert to grams if shown in kg or other units
        4. If multiple numbers are visible, choose the primary weight reading
        5. Return ONLY a JSON object with this exact format:
        {
            "weight_grams": <number>,
            "confidence": "<high|medium|low>",
            "unit_detected": "<g|kg|oz|lb>"
        }

        If the image is unclear or weight cannot be determined, return:
        {
            "weight_grams": null,
            "confidence": "low",
            "unit_detected": "unknown"
        }
        """

        response = model.generate_content([prompt, image])
        response_text = response.text.strip()

        # Parse JSON response
        import json
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        weight = result.get("weight_grams")
        confidence = result.get("confidence", "low")
        unit = result.get("unit_detected", "unknown")

        if weight is None:
            return None, "low", "Could not detect weight from image. Please ensure the scale display is clearly visible."

        # Validate weight is reasonable (0.1g to 10000g)
        if weight < 0.1 or weight > 10000:
            return None, "low", f"Detected weight ({weight}g) seems unrealistic. Please retake the photo."

        message = f"Detected {weight}g ({unit})"
        return float(weight), confidence, message

    except Exception as e:
        return None, "low", f"Error processing image: {str(e)}"


def extract_body_weight_from_image(image_bytes: bytes) -> Tuple[Optional[float], str, str]:
    """
    Extract body weight from weighing scale image using Gemini Vision.

    Args:
        image_bytes: Image bytes of weighing scale

    Returns:
        Tuple of (weight_kg, confidence, message)
        - weight_kg: Extracted weight in kg or None if extraction failed
        - confidence: "high", "medium", or "low"
        - message: Additional information or error message
    """
    try:
        # Load image
        image = Image.open(io.BytesIO(image_bytes))

        # Use Gemini Vision model
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """
        You are analyzing an image of a body weighing scale.

        Instructions:
        1. Look for the body weight displayed on the scale
        2. Extract ONLY the weight number
        3. Convert to kilograms if shown in pounds or other units (1 lb = 0.453592 kg)
        4. Return ONLY a JSON object with this exact format:
        {
            "weight_kg": <number>,
            "confidence": "<high|medium|low>",
            "unit_detected": "<kg|lb|st>"
        }

        If the image is unclear or weight cannot be determined, return:
        {
            "weight_kg": null,
            "confidence": "low",
            "unit_detected": "unknown"
        }
        """

        response = model.generate_content([prompt, image])
        response_text = response.text.strip()

        # Parse JSON response
        import json
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        weight = result.get("weight_kg")
        confidence = result.get("confidence", "low")
        unit = result.get("unit_detected", "unknown")

        if weight is None:
            return None, "low", "Could not detect weight from image. Please ensure the scale display is clearly visible."

        # Validate weight is reasonable (20kg to 300kg for human body weight)
        if weight < 20 or weight > 300:
            return None, "low", f"Detected weight ({weight}kg) seems unrealistic. Please retake the photo."

        message = f"Detected {weight}kg ({unit})"
        return float(weight), confidence, message

    except Exception as e:
        return None, "low", f"Error processing image: {str(e)}"


def chat_with_gemini(message: str, history: list = None, user_context: dict = None) -> str:
    """
    Chat with Gemini Pro for nutrition coaching.

    Args:
        message: User's message
        history: Chat history (list of dicts with 'role' and 'content')
        user_context: Additional context (weight logs, food logs, streak, etc.)

    Returns:
        AI response string
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Build context-aware system prompt
        system_prompt = """
        You are FitWit's AI nutrition coach. You provide personalized guidance on:
        - Meal planning and suggestions
        - Calorie tracking insights
        - Weight trend analysis
        - Motivation and encouragement
        - Nutrition education

        Keep responses concise, friendly, and actionable. Use the user's data to give personalized advice.
        """

        # Add user context if available
        if user_context:
            context_text = "\n\nUser Context:\n"
            if "streak" in user_context:
                context_text += f"- Current streak: {user_context['streak']} days\n"
            if "recent_weight" in user_context:
                context_text += f"- Recent weight: {user_context['recent_weight']}kg\n"
            if "weight_trend" in user_context:
                context_text += f"- Weight trend: {user_context['weight_trend']}\n"
            if "calories_today" in user_context:
                context_text += f"- Calories today: {user_context['calories_today']}\n"

            system_prompt += context_text

        # Build conversation history
        conversation = []
        if history:
            for msg in history:
                conversation.append({
                    "role": msg["role"],
                    "parts": [msg["content"]]
                })

        # Add current message
        conversation.append({
            "role": "user",
            "parts": [f"{system_prompt}\n\nUser: {message}"]
        })

        # Generate response
        chat = model.start_chat(history=conversation[:-1] if len(conversation) > 1 else [])
        response = chat.send_message(conversation[-1]["parts"][0])

        return response.text.strip()

    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}. Please try again."
