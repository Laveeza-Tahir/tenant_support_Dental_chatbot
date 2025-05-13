import re

class StaticInfoNode:
    async def __call__(self, state):
        user_message = state.get("user_message", "").lower()
        
        # Clinic information
        clinic_info = {
            "name": "Dental Health Specialists",
            "address": "123 Dental St, Cityville, CA 90210",
            "phone": "+1-234-567-890",
            "email": "contact@dentalhealthclinic.com",
            "hours": "Monday–Friday, 9AM–5PM",
            "parking": "Free parking available in our garage",
            "public_transport": "Bus routes 10, 15 and 22 stop right outside our clinic"
        }
        
        # Create Google Maps link
        google_maps_link = f"https://www.google.com/maps/search/?api=1&query={clinic_info['address'].replace(' ', '+')}"
        
        # Check if the query is specifically about location/address
        location_query = any(keyword in user_message for keyword in ["location", "address", "where", "office", "directions", "find"])
        
        # Check if query is about parking
        parking_query = "parking" in user_message
        
        # Check if query is about public transport
        transport_query = any(keyword in user_message for keyword in ["bus", "train", "subway", "transport", "metro"])
        
        # Default full contact information
        if location_query:
            # Specific location information
            state["final_response"] = (
                f"📍 Our office is located at:\n"
                f"{clinic_info['address']}\n\n"
                f"🗺️ Find us on Google Maps: {google_maps_link}\n\n"
                f"Need help with directions? Feel free to call us at {clinic_info['phone']}"
            )
        elif parking_query:
            # Parking information
            state["final_response"] = (
                f"🚗 {clinic_info['parking']}\n\n"
                f"Our address is: {clinic_info['address']}\n"
                f"🗺️ Find us on Google Maps: {google_maps_link}"
            )
        elif transport_query:
            # Public transport information
            state["final_response"] = (
                f"🚌 {clinic_info['public_transport']}\n\n"
                f"Our address is: {clinic_info['address']}\n"
                f"🗺️ Find us on Google Maps: {google_maps_link}"
            )
        else:
            # Full contact information
            state["final_response"] = (
                f"📍 {clinic_info['name']} is open {clinic_info['hours']}.\n"
                f"🏢 Address: {clinic_info['address']}\n"
                f"📞 Call us: {clinic_info['phone']}\n"
                f"📧 Email: {clinic_info['email']}\n\n"
                f"🚗 {clinic_info['parking']}\n"
                f"🚌 {clinic_info['public_transport']}\n\n"
                f"🗺️ Find us on Google Maps: {google_maps_link}"
            )
        return state
