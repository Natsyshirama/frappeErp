import frappe
import csv
import io
from datetime import datetime, timedelta

def create_uom_if_not_exists(uom_name):
    """Crée une unité de mesure si elle n'existe pas"""
    if not frappe.db.exists("UOM", uom_name):
        uom = frappe.new_doc("UOM")
        uom.update({
            "doctype": "UOM",
            "uom_name": uom_name,
            "must_be_whole_number": 0,
            "enabled": 1
        })
        uom.insert(ignore_permissions=True)
        frappe.log_error(f"Unité de mesure créée: {uom_name}")

def create_or_update_item(item_name, quantite, unite):
    """Crée ou met à jour un article avec les paramètres spécifiés"""
    # Créer l'UOM si elle n'existe pas
    create_uom_if_not_exists(unite)
    
    # Vérifier si l'article existe déjà par son nom
    existing_item = frappe.db.get_value("Item", {"item_name": item_name}, ["item_code", "name"], as_dict=True)
    
    if existing_item:
        # Utiliser l'article existant
        item_code = existing_item.item_code
        item = frappe.get_doc("Item", existing_item.name)
    else:
        # Générer un nouveau code article selon la convention V001, V002, etc.
        last_item = frappe.db.sql("""
            SELECT item_code FROM `tabItem` 
            WHERE item_code LIKE 'V%' AND LENGTH(item_code) = 4
            ORDER BY CAST(SUBSTRING(item_code, 2) AS UNSIGNED) DESC 
            LIMIT 1
        """, as_dict=True)
        
        if last_item:
            last_number = int(last_item[0]['item_code'][1:])
            item_code = f"V{last_number + 1:03d}"
        else:
            item_code = "V001"
            
        # Créer le nouvel article
        item = frappe.new_doc("Item")
        item.update({
            "item_code": item_code,
            "item_name": item_name,
            "item_group": "Products",
            "stock_uom": unite,
            "is_stock_item": 1,
            "opening_stock": quantite * 2,
            "valuation_rate": 0,
            "standard_rate": 0,
            "description": item_name
        })
        
        # Ajouter l'UOM à la table enfant
        item.append("uoms", {
            "uom": unite,
            "conversion_factor": 1
        })
        
        item.insert(ignore_permissions=True)
        frappe.log_error(f"Article créé: {item_code} - {item_name}")
    
    # Mise à jour du stock si nécessaire
    if item.opening_stock < quantite * 2:
        item.db_set("opening_stock", quantite * 2)
    
    return item_code
def create_payment_entry(invoice):


    """Crée un paiement pour une facture validée"""
    try:
        # Vérifier si le moyen de paiement "Espèces" existe
        if not frappe.db.exists("Mode of Payment", "Espèces"):
            # Créer le moyen de paiement s'il n'existe pas
            mop = frappe.new_doc("Mode of Payment")
            mop.update({
                "mode_of_payment": "Espèces",
                "type": "Cash",
                "accounts": [{
                    "company": invoice.company or "E mark",
                    "default_account": "Cash - EM"
                }]
            })
            mop.insert(ignore_permissions=True)      
        # 1. Créer d'abord l'entrée Sales Invoice Payment
        sip = frappe.new_doc("Sales Invoice Payment")
        sip.update({
            "parent": invoice.name,
            "parenttype": "Sales Invoice",
            "parentfield": "payments",
            "mode_of_payment": "Espèces",
            "amount": invoice.grand_total,
            "account": "Cash - EM",
            "type": "Cash",
            "base_amount": invoice.grand_total,
            "default": 1
        })
        sip.insert(ignore_permissions=True)
        
        # 2. Ensuite créer le Payment Entry
        payment = frappe.new_doc("Payment Entry")
        payment.update({
            "payment_type": "Receive",
            "posting_date": invoice.posting_date,
            "company": invoice.company or "E mark",
            "party_type": "Customer",
            "party": invoice.customer,
            "paid_amount": invoice.grand_total,
            "received_amount": invoice.grand_total,
            "mode_of_payment": "Espèces",
            "reference_no": f"PAY-{invoice.name}",
            "reference_date": invoice.posting_date,
            "paid_from": "Debtors - EM",
            "paid_to": "Cash - EM",
            "references": [{
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice.name,
                "total_amount": invoice.grand_total,
                "outstanding_amount": 0,
                "allocated_amount": invoice.grand_total
            }]
        })
        payment.insert(ignore_permissions=True)
        payment.submit()
        
        # 3. Mettre à jour le statut de la facture
        frappe.db.set_value("Sales Invoice", invoice.name, {
            "status": "Paid",
            "outstanding_amount": 0
        })

    except Exception as e:
        frappe.log_error(f"Erreur création paiement pour {invoice.name}", str(e))
        raise

@frappe.whitelist()
def import_sales_invoice_item_csv(data):
    result_messages = []

    csv_file = io.StringIO(data)
    reader = csv.DictReader(csv_file, delimiter=',')

    invoices_by_customer = {}##dico vide

    for row in reader:
        try:
            customer_name = row['Customer_name']
            item_name = row['Item_name']
            quantite = float(row['quantite'])
            prix = float(row['prix'])
            is_paye = row['is_paye'].strip().lower() == 'yes'
            unite = row.get('unite', 'piece')
            
            if quantite <= 0:
                raise ValueError("La quantité doit être positive")

            # Créer/mettre à jour l'article
            item_code = create_or_update_item(item_name, quantite, unite)

            if customer_name not in invoices_by_customer:
                invoices_by_customer[customer_name] = { #creation structure
                    "customer": customer_name,
                    "posting_date": datetime.now().strftime('%Y-%m-%d'),
                    "due_date": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                    "is_paye": is_paye,
                    "items": []
                }

            invoices_by_customer[customer_name]["items"].append({ #ajout donnee dans le structure
                "item_code": item_code,
                "qty": quantite,
                "rate": prix,
                "uom": unite,
                "stock_uom": unite,
                "conversion_factor": 1.0,
                "income_account": "Sales - EM"
            })
            
        except Exception as e:
            result_messages.append(f"❌ Erreur ligne {reader.line_num}: {str(e)}")
            continue

    for customer_name, invoice_data in invoices_by_customer.items():
        try:
            # Création de la facture
            invoice = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": invoice_data["customer"],
                "posting_date": invoice_data["posting_date"],
                "due_date": invoice_data["due_date"],
                "items": invoice_data["items"],
                "status": "Draft",
                "docstatus": 0
            })
            invoice.insert(ignore_permissions=True)

            # Valider la facture
            invoice.submit()

            if invoice_data["is_paye"]:
                create_payment_entry(invoice)
                result_messages.append(f"✅ Facture PAYÉE créée: {invoice.name}")
            else:
                if datetime.strptime(invoice_data["due_date"], '%Y-%m-%d').date() < datetime.now().date():
                    invoice.db_set("status", "Overdue")
                    result_messages.append(f"✅ Facture EN RETARD créée: {invoice.name}")
                else:
                    result_messages.append(f"✅ Facture IMPAYÉE créée: {invoice.name}")

        except Exception as e:
            result_messages.append(f"❌ Erreur création facture pour {customer_name}: {str(e)}")
            frappe.log_error("Erreur import facture", str(e))

    return "\n".join(result_messages)