"""
Django management command to test HuggingFace API connections

Usage:
    python manage.py test_hf_apis

This command tests all 3 free HuggingFace models used by Lumina:
1. imfarzanansari/skintelligent-acne (acne detection)
2. anismizi/skin-type-classifier (skin type classification)
3. driboune/skin_type (skin properties analysis)
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import time
from pathlib import Path
import cv2
import numpy as np


class Command(BaseCommand):
    help = 'Test HuggingFace API connections for all 3 models'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('LUMINA - HuggingFace API Connection Test'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write('')
        
        # Check if API key is configured
        api_key = settings.HF_API_KEY
        
        if not api_key or api_key == 'your-huggingface-key-here':
            self.stdout.write(self.style.ERROR('❌ HuggingFace API key not configured!'))
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('How to get your FREE HuggingFace API key:'))
            self.stdout.write('1. Go to https://huggingface.co/join')
            self.stdout.write('2. Create a free account')
            self.stdout.write('3. Go to Settings → Access Tokens')
            self.stdout.write('4. Click "New token"')
            self.stdout.write('5. Name it "lumina" and select "read" permission')
            self.stdout.write('6. Click Generate and copy your token (starts with hf_)')
            self.stdout.write('')
            self.stdout.write('Then add it to your .env file:')
            self.stdout.write('HF_API_KEY=hf_your_actual_token_here')
            self.stdout.write('')
            return
        
        self.stdout.write(self.style.SUCCESS(f'✓ API key found: {api_key[:10]}...'))
        self.stdout.write('')
        
        # Create a test image (simple white rectangle)
        test_image = self.create_test_image()
        
        # Test all 3 models
        models = [
            {
                'name': 'Acne Detection (skintelligent-acne)',
                'id': 'imfarzanansari/skintelligent-acne',
                'description': 'Detects acne severity levels 0-3'
            },
            {
                'name': 'Skin Type Classifier',
                'id': 'anismizi/skin-type-classifier',
                'description': 'Classifies skin as oily/dry/normal/combination'
            },
            {
                'name': 'Skin Properties Analyzer',
                'id': 'driboune/skin_type',
                'description': 'Analyzes skin properties and undertone'
            }
        ]
        
        results = []
        
        for i, model in enumerate(models, 1):
            self.stdout.write(self.style.HTTP_INFO(f'[{i}/3] Testing {model["name"]}...'))
            self.stdout.write(f'      Model: {model["id"]}')
            self.stdout.write(f'      Purpose: {model["description"]}')
            
            success, message = self.test_model(model['id'], test_image, api_key)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'      ✓ {message}'))
                results.append(True)
            else:
                self.stdout.write(self.style.ERROR(f'      ✗ {message}'))
                results.append(False)
            
            self.stdout.write('')
            
            # Small delay between tests
            if i < len(models):
                time.sleep(2)
        
        # Summary
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('TEST SUMMARY'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        
        passed = sum(results)
        total = len(results)
        
        if passed == total:
            self.stdout.write(self.style.SUCCESS(f'✓ All {total} models are accessible!'))
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Your Lumina app is ready to analyze skin!'))
            self.stdout.write('')
            self.stdout.write('Note: First scan may take 30-60 seconds if models are cold.')
            self.stdout.write('Subsequent scans will be fast (5-10 seconds).')
        else:
            self.stdout.write(self.style.WARNING(f'⚠ {passed}/{total} models accessible'))
            self.stdout.write('')
            if passed > 0:
                self.stdout.write('Your app will work but some features may be limited.')
            else:
                self.stdout.write('Please check your API key and internet connection.')
        
        self.stdout.write('')
    
    def create_test_image(self):
        """Create a simple test image as bytes"""
        # Create a 224x224 white image
        img = np.ones((224, 224, 3), dtype=np.uint8) * 255
        
        # Add a simple face-like pattern (oval)
        cv2.ellipse(img, (112, 112), (60, 80), 0, 0, 360, (200, 200, 200), -1)
        
        # Encode to JPEG bytes
        success, encoded = cv2.imencode('.jpg', img)
        
        if success:
            return encoded.tobytes()
        else:
            # Fallback: minimal valid JPEG
            return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfe\xb28\xff\xd9'
    
    def test_model(self, model_id, image_bytes, api_key):
        """Test a single HuggingFace model"""
        url = f'https://api-inference.huggingface.co/models/{model_id}'
        headers = {'Authorization': f'Bearer {api_key}'}
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=image_bytes,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return True, f'SUCCESS! Response: {str(data)[:80]}...'
            
            elif response.status_code == 503:
                return True, 'Model is loading (cold start). Will work when needed.'
            
            elif response.status_code == 401:
                return False, 'Invalid API key. Please check your HF_API_KEY.'
            
            elif response.status_code == 429:
                return False, 'Rate limit exceeded. Wait a moment and try again.'
            
            else:
                return False, f'HTTP {response.status_code}: {response.text[:100]}'
        
        except requests.exceptions.Timeout:
            return False, 'Request timeout. Check your internet connection.'
        
        except requests.exceptions.RequestException as e:
            return False, f'Network error: {str(e)[:100]}'
        
        except Exception as e:
            return False, f'Error: {str(e)[:100]}'