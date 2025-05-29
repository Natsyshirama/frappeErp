from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist(allow_guest=True)
def getUsers():
    try:
        required_roles = ["System Manager"]
        user_roles = set(frappe.get_roles())

        if not user_roles.intersection(required_roles):
            return {
                "success": False,
                "message": f"Requires one of these roles: {', '.join(required_roles)}"
            }
        
        # Get all users
        users = frappe.get_all("User",
            filters={"enabled": 1},
            fields=["name", "first_name", "last_name", "email","creation"])
        # Format the response
        formatted_users = []
        for user in users:
            formatted_users.append({
                "name": user.name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "creation": user.creation.strftime("%Y-%m-%d %H:%M:%S")
            })
        return {
            "success": True,
            "users": formatted_users,
            "timestamp": now_datetime()
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API getUsers Error")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def getProfile():
    try:

        user_connecter= frappe.session.user
        if user_connecter == "Guest":
            return {
                "success": False,
                "message": "User not connected"
            }
        # Get the user profile
        user = frappe.get_doc("User", user_connecter)
        # Format the response   
        formatted_user = {
            "name": user.name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "gender": user.gender,
            "creation": user.creation.strftime("%Y-%m-%d %H:%M:%S")
        }
        return {
            "success": True,
            "user": formatted_user,
            "timestamp": now_datetime()
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API getProfile Error")
        return {
            "success": False,
            "message": str(e)
        }