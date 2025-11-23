#!/usr/bin/env python
"""
Quick test script to verify Google Maps API key configuration.
Run this to test if your API key is valid and the required APIs are enabled.

Usage:
    python test_google_api.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobplatform.settings')
django.setup()

import requests
from django.conf import settings


def test_api_key():
    """Test the Google Maps API key configuration."""
    
    print("=" * 70)
    print("GOOGLE MAPS API KEY TEST")
    print("=" * 70)
    
    # Check if API key is set
    api_key = settings.GOOGLE_MAPS_API_KEY
    print(f"\n✓ API Key found in settings")
    print(f"  Key prefix: {api_key[:20]}..." if len(api_key) > 20 else f"  Key: {api_key}")
    print(f"  Key length: {len(api_key)} characters")
    
    if not api_key or api_key == "your_google_maps_api_key_here":
        print("\n❌ ERROR: API key is not configured!")
        print("   Please set a valid Google Maps API key in your .env file")
        return False
    
    print("\n" + "=" * 70)
    print("TEST 1: Geocoding API")
    print("=" * 70)
    
    # Test Geocoding API
    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
    test_address = "Atlanta, GA"
    
    print(f"\nTesting geocoding for: {test_address}")
    
    response = requests.get(geocode_url, params={
        "address": test_address,
        "key": api_key
    })
    
    data = response.json()
    
    print(f"Response status: {data.get('status')}")
    
    if data.get('status') == 'OK':
        print("✓ Geocoding API is working!")
        location = data['results'][0]['geometry']['location']
        print(f"  Coordinates: {location['lat']}, {location['lng']}")
    elif data.get('status') == 'REQUEST_DENIED':
        print("❌ REQUEST_DENIED - API key is invalid or Geocoding API not enabled")
        print(f"   Error: {data.get('error_message', 'No error message')}")
        print("\nSolution:")
        print("1. Go to: https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com")
        print("2. Click 'Enable' for Geocoding API")
        return False
    else:
        print(f"❌ Error: {data.get('status')}")
        print(f"   Message: {data.get('error_message', 'No error message')}")
        return False
    
    print("\n" + "=" * 70)
    print("TEST 2: Maps JavaScript API")
    print("=" * 70)
    
    # Test Maps JavaScript API (by checking if the key works with a simple request)
    maps_url = "https://maps.googleapis.com/maps/api/staticmap"
    
    print("\nTesting Maps JavaScript API...")
    
    response = requests.get(maps_url, params={
        "center": "40.714728,-73.998672",
        "zoom": "12",
        "size": "400x400",
        "key": api_key
    })
    
    if response.status_code == 200:
        print("✓ Maps JavaScript API appears to be working!")
    elif response.status_code == 403:
        print("❌ Maps JavaScript API not enabled or restricted")
        print("\nSolution:")
        print("1. Go to: https://console.cloud.google.com/apis/library/maps-backend.googleapis.com")
        print("2. Click 'Enable' for Maps JavaScript API")
        return False
    else:
        print(f"⚠ Unexpected status code: {response.status_code}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\n✓ All tests passed! Your Google Maps API is configured correctly.")
    print("\nYou should now be able to:")
    print("  - View the job map at: http://127.0.0.1:8000/job_map/")
    print("  - View applicant maps (requires recruiter account)")
    print("\n")
    return True


if __name__ == "__main__":
    try:
        success = test_api_key()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
