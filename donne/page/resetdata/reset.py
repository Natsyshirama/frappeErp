import frappe

@frappe.whitelist()
def reinitialiser_donnees(doctypes):
    import json
    try:
        doctypes = json.loads(doctypes) if isinstance(doctypes, str) else doctypes
    except Exception:
        return {
            "success": False,
            "message": "Format de données invalide pour 'doctypes'.",
            "results": {}
        }

    # Liste des DocTypes autorisés à être réinitialisés
    doctypes_autorises = [
         "Customer",
        "Quotation",
        "Quotation Item",
        "Sales Order",
        "Sales Order Item",
    ]

    results = {}
    frappe.db.sql("SET FOREIGN_KEY_CHECKS = 0")
    
    for doctype in doctypes:
        if doctype in doctypes_autorises:
            table_name = f"tab{doctype}"
            try:
                frappe.db.sql(f"TRUNCATE `{table_name}`")
                results[doctype] = "succès"
            except Exception as e:
                results[doctype] = f"erreur: {str(e)}"
        else:
            results[doctype] = "Non autorisé"
    
    frappe.db.sql("SET FOREIGN_KEY_CHECKS = 1")
    frappe.db.commit()

    return {
        "success": True,
        "results": results,
        "message": f"Réinitialisation terminée pour les DocTypes autorisés"
    }