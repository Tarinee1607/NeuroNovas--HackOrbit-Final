**Check Point-1 : Language Detection and Translation **
    ### 🌐 Language Detection & Translation Support

    Our chatbot enhances inclusivity by incorporating automatic language detection and bidirectional translation, allowing users to communicate in their native language while receiving intelligent responses.
    
    ### 🔍 How It Works

    1. **Language Detection**: The system uses `googletrans` to identify the user's language. If it's not English, the message is translated into English for processing.
  
    2. **English-First Processing**: The translated message goes through our NLP pipeline for classification, emotion detection, and AI response generation using the Mistral API.

    3. **Response Translation**: The English response is translated back into the user's original language.

    4. **Fallback Logic**: If language detection fails, the system defaults to English.

    ### Related Code
    - **translate.py**: Functions for language detection and translation.
    - **requirements.txt**: Includes `googletrans==4.0.0-rc1`.

    This system effectively bridges language barriers, fostering a supportive environment for users seeking help.

**Check Point-2 : Emergency Trigger & Crisis Response Mechanism  **
    If a user's message indicates extreme distress or crisis (e.g., suicidal thoughts, self-harm intent, or violent language), the system detects it as an emergency. It immediately lowers the mental health score       and responds with a compassionate message, urging the user to contact a trusted person or emergency helpline for support.
    give heading.
