#!/usr/bin/env python3
"""
Example script demonstrating how to use the Multi-Agent Design System API.

This script shows how to:
1. Upload images
2. Generate collages
3. Check task status
4. Download results
"""

import requests
import time
import os
from pathlib import Path


def upload_images_and_generate_collage(image_paths, api_base_url="http://localhost:8000"):
    """
    Upload images and generate a collage.
    
    Args:
        image_paths: List of paths to image files
        api_base_url: Base URL of the API server
    """
    
    print("🎨 MyCraftCrew - Collage Generation Example")
    print("=" * 60)
    
    # Check if images exist
    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"❌ Error: Image not found: {image_path}")
            return
    
    print(f"📸 Uploading {len(image_paths)} images...")
    
    # Prepare files for upload
    files = []
    for image_path in image_paths:
        files.append(('files', open(image_path, 'rb')))
    
    try:
        # Upload images
        response = requests.post(
            f"{api_base_url}/api/v1/upload/images",
            files=files
        )
        
        # Close file handles
        for _, file_handle in files:
            file_handle.close()
        
        if response.status_code == 200:
            result = response.json()
            task_id = result['task_id']
            print(f"✅ Images uploaded successfully!")
            print(f"📋 Task ID: {task_id}")
            
            # Wait for processing
            print("⏳ Waiting for collage generation...")
            while True:
                status_response = requests.get(f"{api_base_url}/api/v1/task/{task_id}")
                
                if status_response.status_code == 200:
                    task_data = status_response.json()['task']
                    status = task_data['status']
                    
                    print(f"📊 Status: {status}")
                    
                    if status == 'completed':
                        print("🎉 Collage generation completed!")
                        
                        # Download the result
                        result_response = requests.get(f"{api_base_url}/api/v1/task/{task_id}/result")
                        
                        if result_response.status_code == 200:
                            # Save the collage
                            output_filename = f"collage_{task_id}.jpg"
                            with open(output_filename, 'wb') as f:
                                f.write(result_response.content)
                            
                            print(f"💾 Collage saved as: {output_filename}")
                            return output_filename
                        else:
                            print(f"❌ Failed to download result: {result_response.status_code}")
                            return None
                    
                    elif status == 'failed':
                        print(f"❌ Task failed: {task_data.get('error_message', 'Unknown error')}")
                        return None
                    
                    elif status in ['pending', 'in_progress']:
                        time.sleep(2)  # Wait 2 seconds before checking again
                        continue
                    
                    else:
                        print(f"❓ Unknown status: {status}")
                        return None
                
                else:
                    print(f"❌ Failed to check status: {status_response.status_code}")
                    return None
        
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on", api_base_url)
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def check_server_health(api_base_url="http://localhost:8000"):
    """Check if the server is running and healthy."""
    try:
        response = requests.get(f"{api_base_url}/api/v1/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Server is healthy!")
            print(f"📊 Version: {health_data.get('version', 'Unknown')}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on", api_base_url)
        return False


def main():
    """Main function to run the example."""
    
    # Check server health first
    if not check_server_health():
        print("\n💡 To start the server, run:")
        print("   cd multi_agent_design_system")
        print("   python3 main.py")
        return
    
    print()
    
    # Example image paths (you can modify these)
    example_images = [
        "example1.jpg",
        "example2.jpg", 
        "example3.jpg"
    ]
    
    # Check if example images exist, if not, create some dummy ones
    if not all(os.path.exists(img) for img in example_images):
        print("📝 Creating example images...")
        try:
            from PIL import Image
            
            # Create some simple colored squares as example images
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
            
            for i, color in enumerate(colors):
                img = Image.new('RGB', (200, 200), color)
                img.save(f"example{i+1}.jpg")
                print(f"   Created example{i+1}.jpg")
            
            example_images = [f"example{i+1}.jpg" for i in range(len(colors))]
            
        except ImportError:
            print("❌ PIL not available. Please provide your own images.")
            print("   Place some .jpg files in the current directory and modify the script.")
            return
    
    # Generate collage
    result_file = upload_images_and_generate_collage(example_images)
    
    if result_file:
        print(f"\n🎊 Success! Your collage is ready: {result_file}")
        print("\n📚 API Documentation available at:")
        print("   http://localhost:8000/docs")
    else:
        print("\n😞 Collage generation failed. Check the logs above.")


if __name__ == "__main__":
    main()
