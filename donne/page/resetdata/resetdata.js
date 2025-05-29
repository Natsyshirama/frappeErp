frappe.pages['resetdata'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Reset Data (Achats)',
        single_column: true
    });

    // Liste des DocTypes spécifiques à afficher
    const allowed_doctypes = [
        "Material Request Item",
        "Material Request",
        "Request for Quotation Item",
        "Request for Quotation",
        "Supplier Quotation",
        "Supplier Quotation Item",
        "Supplier",
        "Item",
        "Purchase Invoice",
        "Purchase Invoice Item",
        "Purchase Order",
        "Purchase Order Item",
        "Payment Entry",
        "Payment Entry Reference",
        "Purchase Receipt",
        "Purchase Receipt Item"
    ];

    // Construire directement l'UI avec les DocTypes autorisés
    build_ui(wrapper, allowed_doctypes.map(name => ({name: name})));

    function build_ui(wrapper, doctypes) {
        $(wrapper).find('.layout-main-section').html(`
            <div class="reset-container" style="margin: 30px;">
                <div class="row">
                    <div class="col-md-6">
                        <h4>DocTypes Achats (${doctypes.length})</h4>
                        <div class="alert alert-info">
                            Seuls les DocTypes liés aux achats sont affichés
                        </div>
                        <div class="input-group" style="margin-bottom: 15px;">
                            <input type="text" id="doctype-search" class="form-control" placeholder="Rechercher...">
                            <span class="input-group-btn">
                                <button class="btn btn-default" type="button" id="search-clear">
                                    <i class="fa fa-times"></i>
                                </button>
                            </span>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <button class="btn btn-xs btn-default" id="select-all">
                                <i class="fa fa-check-square-o"></i> Tout
                            </button>
                            <button class="btn btn-xs btn-default" id="deselect-all">
                                <i class="fa fa-square-o"></i> Rien
                            </button>
                        </div>
                        <div id="doctype-list" style="max-height: 60vh; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">
                            <table class="table table-condensed">
                                <tbody>
                                    ${doctypes.map(d => `
                                        <tr>
                                            <td><input type="checkbox" class="doctype-checkbox" value="${d.name}" id="dt-${d.name}"></td>
                                            <td><label for="dt-${d.name}" style="font-weight: normal; cursor: pointer;">${d.name}</label></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h4>Actions</h4>
                        <div class="alert alert-danger">
                            <i class="fa fa-warning"></i> 
                            <strong>Attention :</strong> Suppression irréversible des données.
                        </div>
                        <div class="well" id="selected-count">
                            <i class="fa fa-list"></i> 
                            <span id="count">0</span> DocType(s) sélectionné(s)
                        </div>
                        <button class="btn btn-danger btn-lg btn-block" id="btn-reset-donnees">
                            <i class="fa fa-trash"></i> Vider les sélections
                        </button>
                    </div>
                </div>
            </div>
        `);

        let selected_doctypes_map = {};

        $('#doctype-search').on('keyup', function() {
            const searchText = $(this).val().toLowerCase();
            $('#doctype-list tr').each(function() {
                const $row = $(this);
                const doctypeName = $row.text().toLowerCase();
                $row.toggle(doctypeName.includes(searchText));
            });
            $('#doctype-list tr:visible .doctype-checkbox').each(function() {
                const val = $(this).val();
                $(this).prop('checked', !!selected_doctypes_map[val]);
            });
            updateSelectionCount();
        });

        $('#search-clear').click(() => $('#doctype-search').val('').trigger('keyup'));

        $(document).on('change', '.doctype-checkbox', function() {
            const name = $(this).val();
            $(this).is(':checked') ? selected_doctypes_map[name] = true : delete selected_doctypes_map[name];
            updateSelectionCount();
        });

        $('#select-all').click(function() {
            $('#doctype-list tr:visible .doctype-checkbox').each(function() {
                $(this).prop('checked', true);
                selected_doctypes_map[$(this).val()] = true;
            });
            updateSelectionCount();
        });

        $('#deselect-all').click(function() {
            $('#doctype-list tr:visible .doctype-checkbox').each(function() {
                $(this).prop('checked', false);
                delete selected_doctypes_map[$(this).val()];
            });
            updateSelectionCount();
        });

        function updateSelectionCount() {
            const selectedCount = Object.keys(selected_doctypes_map).length;
            $('#selected-count #count').text(selectedCount);
            $('#selected-count').toggleClass('well-danger', selectedCount > 0);
        }

        $('#btn-reset-donnees').on('click', function() {
            const selected_doctypes = Object.keys(selected_doctypes_map);
            if (selected_doctypes.length === 0) {
                frappe.msgprint({ 
                    title: __('Aucune sélection'), 
                    message: __('Veuillez sélectionner au moins un DocType.'), 
                    indicator: 'red' 
                });
                return;
            }
    
            frappe.confirm(
                `<h4>Confirmer la suppression</h4>
                <p>Vous allez supprimer les données de :</p>
                <ul class="list-unstyled" style="max-height: 200px; overflow-y: auto;">
                    ${selected_doctypes.map(d => `<li><i class="fa fa-table"></i> ${d}</li>`).join('')}
                </ul>
                <p class="text-danger"><strong>Cette action ne peut pas être annulée !</strong></p>`,
                function() {
                    frappe.call({
                        method: 'erpnext.donne.page.resetdata.reset.reinitialiser_donnees',
                        args: { 'doctypes': selected_doctypes },
                        callback: function(r) {
                            if (r.message) {
                                let details = '';
                                if (r.results) {
                                    details = '<ul style="max-height: 200px; overflow-y: auto;">';
                                    for (const [doctype, result] of Object.entries(r.results)) {
                                        const icon = result === "succès" ? "✅" : result === "Non autorisé" ? "⚠️" : "❌";
                                        details += `<li>${icon} <b>${doctype}</b> : ${result}</li>`;
                                    }
                                    details += '</ul>';
                                }
                                
                                frappe.show_alert({
                                    message: __('Réinitialisation terminée'),
                                    indicator: r.success ? 'green' : 'red'
                                }, 5);

                                frappe.msgprint({
                                    title: __('Résultat de la réinitialisation'),
                                    message: `${r.message}${details}`,
                                    indicator: r.success ? 'green' : 'red',
                                    wide: true
                                });
                            }
                        },
                        freeze: true,
                        freeze_message: __('Nettoyage des données...')
                    });
                },
                null,
                __('Confirmation'),
                __('Supprimer'),
                true
            );
        });
    }
};