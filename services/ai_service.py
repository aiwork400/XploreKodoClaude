"""
AI Service
OpenAI integration for chat widget
"""
import os
from typing import List, Dict, Optional
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class AIService:
    """AI chat service using OpenAI"""
    
    SYSTEM_PROMPTS = {
        "en": """You are a helpful assistant for XploraKodo, a Japanese language learning platform.
You help students with:
- Learning Japanese (N5-N1 levels)
- Understanding lessons and quizzes
- Career guidance for working in Japan
- Platform navigation and features

Be friendly, encouraging, and concise. Always respond in English unless asked otherwise.""",
        
        "ne": """तपाईं XploraKodo को लागि एक सहयोगी सहायक हुनुहुन्छ, जुन जापानी भाषा सिक्ने प्लेटफर्म हो।
तपाईं विद्यार्थीहरूलाई यी कुराहरूमा मद्दत गर्नुहुन्छ:
- जापानी भाषा सिक्ने (N5-N1 स्तरहरू)
- पाठ र क्विजहरू बुझ्ने
- जापानमा काम गर्ने करियर मार्गदर्शन
- प्लेटफर्म नेभिगेसन र सुविधाहरू

मित्रवत, प्रोत्साहनजनक र संक्षिप्त हुनुहोस्। जबसम्म अन्यथा सोधिएन नेपालीमा जवाफ दिनुहोस्।""",
        
        "ja": """あなたはXploraKodoのアシスタントです。日本語学習プラットフォームです。
学生を以下の点でサポートします：
- 日本語学習（N5-N1レベル）
- レッスンとクイズの理解
- 日本での就職に関するキャリアガイダンス
- プラットフォームのナビゲーションと機能

親切で、励まし、簡潔に対応してください。特に指示がない限り日本語で回答してください。"""
    }
    
    @staticmethod
    async def chat(
        messages: List[Dict[str, str]],
        language: str = "en",
        model: str = "gpt-4o-mini"
    ) -> tuple[str, int]:
        """
        Send chat request to OpenAI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            language: Language code (en, ne, ja)
            model: OpenAI model to use
            
        Returns:
            Tuple of (response_content, tokens_used)
        """
        # Add system prompt
        system_prompt = AIService.SYSTEM_PROMPTS.get(language, AIService.SYSTEM_PROMPTS["en"])
        
        full_messages = [
            {"role": "system", "content": system_prompt}
        ] + messages
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            return content, tokens
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    @staticmethod
    async def generate_conversation_title(
        first_message: str,
        language: str = "en"
    ) -> str:
        """
        Generate a short title for the conversation
        
        Args:
            first_message: User's first message
            language: Language code
            
        Returns:
            Short title (max 50 chars)
        """
        prompts = {
            "en": f"Generate a very short title (max 5 words) for a conversation starting with: '{first_message[:100]}'",
            "ne": f"यो कुराकानीको लागि एक छोटो शीर्षक (अधिकतम 5 शब्द) उत्पन्न गर्नुहोस्: '{first_message[:100]}'",
            "ja": f"次の会話の短いタイトル（最大5語）を生成してください: '{first_message[:100]}'"
        }
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Generate a very short conversation title. Respond with ONLY the title, no quotes or punctuation."},
                    {"role": "user", "content": prompts.get(language, prompts["en"])}
                ],
                temperature=0.5,
                max_tokens=20
            )
            
            title = response.choices[0].message.content.strip().strip('"').strip("'")
            return title[:50]  # Ensure max 50 chars
            
        except Exception:
            # Fallback to simple title
            return first_message[:47] + "..." if len(first_message) > 47 else first_message
