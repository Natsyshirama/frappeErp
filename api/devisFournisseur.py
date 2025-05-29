from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist()
def get_supplier_quotations(supplier=None, from_date=None, to_date=None, status=None):
    """
    Récupère la liste des devis fournisseurs avec filtres optionnels
    Args:
        supplier (str): Nom du fournisseur pour filtrer
        from_date (str): Date de début au format YYYY-MM-DD
        to_date (str): Date de fin au format YYYY-MM-DD
        status (str): Statut à filtrer (Draft, Submitted, Cancelled)
    """
    try:
        # Vérification des permissions
        if frappe.session.user == "Guest":
            frappe.throw(_("Authentification requise"), frappe.AuthenticationError)

        # Préparation des filtres de base
        filters = {"docstatus": ["!=", 2]}  # Exclut les documents supprimés
        
        # Ajout des filtres optionnels
        if supplier:
            filters["supplier"] = supplier
            
        if status:
            filters["status"] = status
            
        if from_date and to_date:
            filters["transaction_date"] = ["between", [getdate(from_date), getdate(to_date)]]
        elif from_date:
            filters["transaction_date"] = [">=", getdate(from_date)]
        elif to_date:
            filters["transaction_date"] = ["<=", getdate(to_date)]

        # Récupération des devis avec champs étendus
        quotations = frappe.get_all("Supplier Quotation",
            filters=filters,
            fields=[
                "name", 
                "supplier", 
                "supplier_name",
                "status",
                "transaction_date",
                "valid_till",
                "grand_total",
                "currency",
                "creation",
                "owner",
                "docstatus"
            ],
            order_by="transaction_date desc, creation desc"
        )
        
        # Formatage de la réponse
        formatted_quotations = []
        for quote in quotations:
            formatted_quotations.append({
                "id": quote.name,
                "supplier": {
                    "id": quote.supplier,
                    "name": quote.supplier_name
                },
                "status": quote.status,
                "dates": {
                    "transaction": quote.transaction_date.strftime("%Y-%m-%d") if quote.transaction_date else None,
                    "valid_till": quote.valid_till.strftime("%Y-%m-%d") if quote.valid_till else None,
                    "created": quote.creation.strftime("%Y-%m-%d %H:%M:%S")
                },
                "amount": {
                    "total": quote.grand_total,
                    "currency": quote.currency
                },
                "meta": {
                    "owner": quote.owner,
                    "docstatus": quote.docstatus  # 0=Draft, 1=Submitted, 2=Cancelled
                }
            })
            
        return {
            "success": True,
            "count": len(quotations),
            "quotations": formatted_quotations,
            "timestamp": now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        frappe.log_error(
            title="Erreur API get_supplier_quotations",
            message=frappe.get_traceback()
        )
        return {
            "success": False,
            "message": "Erreur lors de la récupération des devis",
            "error": str(e)
        }
@frappe.whitelist()
def get_quotation_details(quotation_name):
    """Récupère les détails d'un devis fournisseur"""
    try:
        if frappe.session.user == "Guest":
            frappe.throw(_("Authentication failed"), frappe.AuthenticationError)

        # Récupération du devis
        quote = frappe.get_doc("Supplier Quotation", quotation_name)
        
        # Récupération des articles
        items = []
        for item in quote.items:
            items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "description": item.description,
                "qty": item.qty,
                "rate": item.rate,
                "amount": item.amount,
                "uom": item.uom
            })
        
        # Formatage de la réponse
        return {
            "success": True,
            "quotation": {
                "name": quote.name,
                "supplier_name": quote.supplier_name,
                "status": quote.status,
                "transaction_date": quote.transaction_date.strftime("%Y-%m-%d") if quote.transaction_date else None,
                "creation": quote.creation.strftime("%Y-%m-%d %H:%M:%S"),
                "items": items
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API get_quotation_details Error")
        return {
            "success": False,
            "message": str(e)
        }
@frappe.whitelist()
def update_item_rate(quotation_name, item_code, new_rate):
    try:
        # ===== 1. VÉRIFICATIONS INITIALES =====
        if frappe.session.user == "Guest":
            return {"success": False, "message": "Authentification requise"}

        if not frappe.db.exists("Supplier Quotation", quotation_name):
            return {"success": False, "message": "Devis introuvable"}

        # ===== 2. RÉCUPÉRATION DU DEVIS ORIGINAL =====
        original_quote = frappe.get_doc("Supplier Quotation", quotation_name)
        
        # ===== 3. GESTION DU STATUT ORIGINAL =====
        # Si le devis est soumis (docstatus=1), on doit d'abord l'annuler
        if original_quote.docstatus == 1:
            original_quote.cancel()
            frappe.db.commit()
            original_quote.reload()
        
        # ===== 4. CRÉATION D'UNE NOUVELLE VERSION =====
        new_quote = frappe.copy_doc(original_quote)
        new_quote.docstatus = 0
        
        # On ne met amended_from que si l'original est annulé
        if original_quote.docstatus == 2:
            new_quote.amended_from = quotation_name
        
        # ===== 5. MISE À JOUR DU PRIX =====
        item_updated = False
        for item in new_quote.items:
            if item.item_code == item_code:
                item.rate = float(new_rate)
                item.amount = float(item.qty) * float(new_rate)
                item_updated = True
                break

        if not item_updated:
            return {"success": False, "message": "Article non trouvé"}

        # ===== 6. SAUVEGARDE ET VALIDATION =====
        new_quote.insert(ignore_permissions=True)
        new_quote.submit()
        frappe.db.commit()

        return {
            "success": True,
            "message": "Nouveau devis créé et validé avec succès",
            "new_quotation_name": new_quote.name,
            "docstatus": new_quote.docstatus,  # 1 (Submitted)
            "status": new_quote.status,  # "Submitted"
            "original_status": "Cancelled" if original_quote.docstatus == 2 else "Draft"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Erreur API update_item_rate")
        return {
            "success": False,
            "message": str(e),
            "error_detail": frappe.get_traceback()
        }