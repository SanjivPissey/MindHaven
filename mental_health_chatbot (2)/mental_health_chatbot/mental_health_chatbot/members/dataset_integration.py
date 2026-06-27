"""
Integrate Mental Health datasets to improve chatbot prompts
Downloads and processes datasets from Kaggle and Hugging Face
"""
import os
import json
from pathlib import Path

try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("⚠️  Hugging Face datasets library not installed. Install with: pip install datasets")

# Dataset paths
DATASETS_DIR = Path(__file__).parent / 'datasets'
DATASETS_DIR.mkdir(exist_ok=True)

def download_huggingface_datasets():
    """Download mental health counseling conversation datasets from Hugging Face"""
    if not DATASETS_AVAILABLE:
        print("❌ Cannot download datasets - libraries not installed")
        return None
    
    datasets_info = []
    
    try:
        # Dataset 1: Mental Health Counseling Conversations
        print("📥 Downloading: Mental Health Counseling Conversations...")
        dataset1 = load_dataset("Amod/mental_health_counseling_conversations")
        datasets_info.append({
            'name': 'Mental Health Counseling Conversations',
            'source': 'Hugging Face - Amod/mental_health_counseling_conversations',
            'data': dataset1,
            'type': 'conversations'
        })
        print(f"✅ Downloaded: {len(dataset1.get('train', []))} training examples")
    except Exception as e:
        print(f"⚠️  Could not download dataset 1: {e}")
    
    try:
        # Dataset 2: Mental Health Conversational Data
        print("📥 Downloading: Mental Health Conversational Data...")
        dataset2 = load_dataset("Ayansk11/Mental_health_data_conversational")
        datasets_info.append({
            'name': 'Mental Health Conversational Data',
            'source': 'Hugging Face - Ayansk11/Mental_health_data_conversational',
            'data': dataset2,
            'type': 'conversational'
        })
        print(f"✅ Downloaded dataset 2")
    except Exception as e:
        print(f"⚠️  Could not download dataset 2: {e}")
    
    return datasets_info

def extract_conversation_examples(datasets_info, num_examples=10):
    """Extract conversation examples from datasets for few-shot learning"""
    examples = []
    
    for dataset_info in datasets_info:
        try:
            data = dataset_info['data']
            # Access train split properly
            if 'train' in data:
                train_data = data['train']
            elif hasattr(data, 'get'):
                train_data = data.get('train', [])
            else:
                print(f"⚠️  Cannot access train data from {dataset_info['name']}")
                continue
            
            if not train_data or len(train_data) == 0:
                print(f"⚠️  No training data found in {dataset_info['name']}")
                continue
            
            print(f"📊 Processing {len(train_data)} examples from {dataset_info['name']}...")
            
            # Extract examples - limit to num_examples
            count = 0
            for i, item in enumerate(train_data):
                if count >= num_examples:
                    break
                
                example = None
                
                # Handle Context-Response format (most common)
                if 'Context' in item and 'Response' in item:
                    context = str(item.get('Context', '')).strip()
                    response = str(item.get('Response', '')).strip()
                    
                    if context and response and len(context) > 10 and len(response) > 20:
                        example = {
                            'user_message': context[:500],  # Limit length
                            'bot_response': response[:500],
                            'source': dataset_info['name']
                        }
                
                # Handle conversations format
                elif 'conversations' in item:
                    conversations = item['conversations']
                    user_msg = ""
                    bot_msg = ""
                    
                    if isinstance(conversations, list):
                        for conv in conversations:
                            if isinstance(conv, dict):
                                if conv.get('from') == 'human' or conv.get('role') == 'user':
                                    user_msg = str(conv.get('value', conv.get('content', ''))).strip()
                                elif conv.get('from') == 'assistant' or conv.get('role') == 'assistant':
                                    bot_msg = str(conv.get('value', conv.get('content', ''))).strip()
                    
                    if user_msg and bot_msg and len(user_msg) > 10 and len(bot_msg) > 20:
                        example = {
                            'user_message': user_msg[:500],
                            'bot_response': bot_msg[:500],
                            'source': dataset_info['name']
                        }
                
                # Handle instruction-output format
                elif 'instruction' in item and 'output' in item:
                    instruction = str(item.get('instruction', item.get('input', ''))).strip()
                    output = str(item.get('output', '')).strip()
                    
                    if instruction and output and len(instruction) > 10 and len(output) > 20:
                        example = {
                            'user_message': instruction[:500],
                            'bot_response': output[:500],
                            'source': dataset_info['name']
                        }
                
                if example:
                    examples.append(example)
                    count += 1
            
            print(f"✅ Extracted {count} examples from {dataset_info['name']}")
        
        except Exception as e:
            print(f"⚠️  Error extracting from {dataset_info['name']}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return examples

def create_few_shot_prompt(examples, max_examples=5):
    """Create a few-shot learning prompt from examples"""
    if not examples:
        return ""
    
    prompt = "\n\nHere are some examples of empathetic, caring mental health support responses that show genuine care, comfort, and ask questions to understand more:\n\n"
    
    for i, example in enumerate(examples[:max_examples]):
        prompt += f"Example {i+1}:\n"
        prompt += f"User: {example['user_message']}\n"
        prompt += f"Bot: {example['bot_response']}\n\n"
    
    prompt += "Notice how these examples show genuine care, comfort the user, validate their feelings, and ask questions to understand more. Use these as inspiration for your response style - be empathetic, validating, caring, comforting, and always show genuine interest in understanding the user better by asking thoughtful follow-up questions.\n"
    
    return prompt

def save_examples_to_file(examples, filename='conversation_examples.json'):
    """Save extracted examples to a JSON file"""
    filepath = DATASETS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(examples)} examples to {filepath}")
    return filepath

def load_examples_from_file(filename='conversation_examples.json'):
    """Load saved examples from file"""
    filepath = DATASETS_DIR / filename
    
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        examples = json.load(f)
    
    return examples

def get_enhanced_system_prompt():
    """Get enhanced system prompt based on dataset patterns"""
    prompt = """You are a warm, deeply empathetic mental health support chatbot trained on real mental health counseling conversations. Your responses are based on proven therapeutic techniques and empathetic communication patterns.

KEY PRINCIPLES FROM TRAINING DATA:
1. Active Listening: Acknowledge what the user has shared by referencing specific details
2. Validation: Always validate emotions - "Your feelings are completely valid" / "It makes sense that you feel..."
3. Empathy: Use "I" statements to show personal connection - "I can understand why..." / "I hear how difficult this is..."
4. Non-judgmental: Never minimize or dismiss feelings - accept them as they are
5. Person-centered: Focus on the user's experience, not generic advice
6. Context awareness: Reference previous parts of the conversation naturally
7. Warmth: Sound like a caring friend or therapist, not a clinical robot

RESPONSE PATTERNS FROM TRAINING:
- Start with validation: "I can hear that..." / "It sounds like..."
- Show understanding: "That must be really difficult" / "I can understand why you feel..."
- Offer perspective: "What you're experiencing is..." / "Many people feel..."
- End with support: "I'm here with you" / "You're not alone in this"

AVOID:
- Generic phrases like "I'm sorry you feel that way" without specifics
- Minimizing language: "It's not that bad" / "At least..."
- Giving unsolicited advice
- Sounding robotic or scripted"""
    
    return prompt

if __name__ == "__main__":
    print("=" * 60)
    print("  DOWNLOADING MENTAL HEALTH DATASETS")
    print("=" * 60)
    print()
    
    # Download datasets
    datasets_info = download_huggingface_datasets()
    
    if datasets_info:
        print()
        print("=" * 60)
        print("  EXTRACTING CONVERSATION EXAMPLES")
        print("=" * 60)
        print()
        
        # Extract examples
        examples = extract_conversation_examples(datasets_info, num_examples=20)
        
        if examples:
            # Save examples
            save_examples_to_file(examples)
            
            print()
            print(f"✅ Successfully extracted {len(examples)} conversation examples")
            print("   These will be used to improve chatbot responses!")
        else:
            print("⚠️  No examples extracted")
    else:
        print()
        print("💡 TIP: Install required libraries:")
        print("   pip install datasets")
        print()
        print("   Or manually download datasets from:")
        print("   - https://huggingface.co/datasets/Amod/mental_health_counseling_conversations")
        print("   - https://huggingface.co/datasets/Ayansk11/Mental_health_data_conversational")

