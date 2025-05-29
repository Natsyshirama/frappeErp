import frappe
import csv
import io
from datetime import datetime, timedelta

@frappe.whitelist()
def import_csv(data):
    result_messages = []

    # Lire le CSV depuis le texte
    csv_file = io.StringIO(data)
    reader = csv.DictReader(csv_file, delimiter=',')  # \t car ton CSV est tabulé

    for row in reader:
        supplier_name = row.get('supplier_name')
        supplier_type = (row.get("type") or "").lower()
        supplier_country = row.get('country')
        naming_series = "SUP-.YYYY.-"
        supplier_doc = frappe.new_doc("Supplier")
        default_price_list = "Standard Buying"
        supplier_groupe = "Local"

        supplier_doc.update({
            "supplier_name": supplier_name,
            "supplier_type": supplier_type.capitalize(),
            "naming_series": naming_series,
           "default_price_list": default_price_list,
            "supplier_groupe": supplier_groupe,
        })

        try:
            supplier_doc.insert(ignore_permissions=True)
            result_messages.append(f"✅ fournisseur '{supplier_name}' ajouté avec succès.")
        except frappe.DuplicateEntryError:
            result_messages.append(f"⚠️ fournisseur '{supplier_name}' existe déjà.")
        except Exception as e:
            result_messages.append(f"❌ Erreur lors de l'ajout de '{supplier_name}': {str(e)}")

    return result_messages
