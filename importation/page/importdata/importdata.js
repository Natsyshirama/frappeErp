frappe.pages['importdata'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Import Data',
        single_column: true
    });

    // Ajouter un input uploade fichier csv
    $(page.body).append(`
        <div style="padding: 20px;">
            <input type="file" id="csv_file" accept=".csv" />
            <button class="btn btn-primary" id="upload_csv">Importer Supplier</button>
        </div>
    `);


    // event inmport client
    $('#upload_csv').on('click', function() {
        let file = document.getElementById('csv_file').files[0];
        if (!file.name.endsWith('.csv')) {
            frappe.msgprint(__('Le fichier doit être un CSV.'));
            return;
        }
        if (!file) {
            frappe.msgprint(__('Veuillez choisir un fichier CSV.'));
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            let content = e.target.result;

            frappe.call({
                method: 'erpnext.importation.page.importdata.importData.import_csv',
                args: {
                    data: content
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        
                        frappe.show_alert({
                            message: __("Importation terminée - {0} lignes traitées", [r.message.length]),
                            indicator: 'green'
                        }, 8);
                        
                        r.message.forEach(msg => {
                            if (msg.includes("✅")) {
                                frappe.show_alert({
                                    message: msg,
                                    indicator: 'green'
                                }, 8);
                            } else if (msg.includes("⚠️")) {
                                frappe.show_alert({
                                    message: msg,
                                    indicator: 'orange'
                                }, 8);
                            } else if (msg.includes("❌")) {
                                frappe.show_alert({
                                    message: msg,
                                    indicator: 'red'
                                }, 8);
                            }
                        });
                    }
                }
            });
        };
        reader.readAsText(file);
    });

   // Dans votre frappe.pages['importdata'].on_page_load
$(page.body).append(`
    <div style="padding: 20px;">
        <h4>Importer Devis Fournisseur</h4>
        <div>
            <label>Fichier Articles (CSV):</label>
            <input type="file" id="devis_items_file" accept=".csv" />
        </div>
        <div>
            <label>Fichier Fournisseurs (CSV):</label>
            <input type="file" id="devis_suppliers_file" accept=".csv" />
        </div>
        <button class="btn btn-primary" id="upload_devis">Importer Devis</button>
    </div>
`);

$('#upload_devis').on('click', function() {
    const items_file = document.getElementById('devis_items_file').files[0];
    const suppliers_file = document.getElementById('devis_suppliers_file').files[0];
    
    if (!items_file || !suppliers_file) {
        frappe.msgprint(__('Veuillez sélectionner les deux fichiers CSV.'));
        return;
    }
    
    const reader1 = new FileReader();
    const reader2 = new FileReader();
    
    reader1.onload = function(e1) {
        reader2.onload = function(e2) {
            frappe.call({
                method: 'erpnext.importation.page.importdata.importDevis.import_supplier_quotations',
                args: {
                    items_data: e1.target.result,
                    suppliers_data: e2.target.result
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __("Importation terminée - {0} résultats", [r.message.length]),
                            indicator: 'green'
                        }, 8);
                        
                        r.message.forEach(msg => {
                            const indicator = msg.includes("✅") ? 'green' : 
                                           msg.includes("⚠️") ? 'orange' : 'red';
                            frappe.show_alert({
                                message: msg,
                                indicator: indicator
                            }, 8);
                        });
                    }
                },
                freeze: true,
                freeze_message: __("Importation des devis en cours...")
            });
        };
        reader2.readAsText(suppliers_file);
    };
    reader1.readAsText(items_file);
});
};