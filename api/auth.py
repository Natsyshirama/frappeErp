from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.auth import LoginManager
from frappe.utils.password import get_decrypted_password
import json

@frappe.whitelist(allow_guest=True)
def signup(email, first_name, last_name, password):
    """API pour l'inscription d'un nouvel utilisateur"""
    try:
        if frappe.db.exists("User", email):
            return {"success": False, "message": "L'utilisateur existe déjà"}

        user = frappe.new_doc("User")
        user.update({
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "send_welcome_email": 0,
            "user_type": "Website User"
        })
        user.new_password = password
        user.insert(ignore_permissions=True)
        
        # Assigner le role 'Customer' par defaut
        user.add_roles("Customer")
        
        return {"success": True, "message": "Compte créé avec succès"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Signup Error")
        return {"success": False, "message": str(e)}
    
@frappe.whitelist(allow_guest=True)
def login(email, password):
    """Endpoint fonctionnel pour l'authentification"""
    try:
        # verification user
        if not frappe.db.exists("User", email):
            frappe.throw(_("User not found"), frappe.DoesNotExistError)

        # Authentification 
        login_manager = LoginManager()
        login_manager.authenticate(email, password)
        login_manager.post_login()

        # Verifictio session
        if frappe.session.user == "Guest":
            frappe.throw(_("Authentication failed"), frappe.AuthenticationError)

        # generer token
        api_key = frappe.generate_hash(length=40)
        frappe.db.set_value("User", email, "api_key", api_key)

        return {
            "success": True,
            "api_key": api_key,
            "user": email
        }

    except Exception as e:
        frappe.log_error("Login API Error", str(e))
        frappe.throw(_(str(e)))
@frappe.whitelist(allow_guest=True)
def logout():
    """Endpoint fonctionnel pour la déconnexion"""
    try:
        if frappe.session.user == "Guest":
            return {
                "success": False,
                "message": "Aucun utilisateur connecté"
            }

        # Méthode moderne de déconnexion
        frappe.local.login_manager.logout()
        frappe.db.commit()
        
        return {
            "success": True,
            "message": "Déconnexion réussie"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Logout Error")
        return {
            "success": False,
            "message": "Échec de la déconnexion",
            "error": str(e)
        }
@frappe.whitelist()
def protected_endpoint():
    """Exemple de point de terminaison protégé"""
    if frappe.session.user == "Guest":
        frappe.throw("Accès non autorisé", frappe.AuthenticationError)
    
    return {
        "success": True,
        "message": "Accès autorisé",
        "user": frappe.session.user
    }