frappe.pages['pagereset'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Reset des données',
        single_column: true
    });

    // Stockage persistant des selections
    let selected_doctypes_map = {};

    // 1. Récupération de TOUS les DocTypes sans limite
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'DocType',
            fields: ['name'],
            limit_page_length: 0,
            order_by: 'name'
        },
        callback: function(r) {
            if (r.message) {
                build_ui(wrapper, r.message);
            }
        }
    });

    function build_ui(wrapper, doctypes) {
        $(wrapper).find('.layout-main-section').html(`
            <div class="reset-container" style="margin: 30px;">
                <div class="row">
                    <div class="col-md-6">
                        <h4>Tous les DocTypes (${doctypes.length})</h4>
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
                                            <td>
                                                <input type="checkbox" class="doctype-checkbox" value="${d.name}" id="dt-${d.name}">
                                            </td>
                                            <td>
                                                <label for="dt-${d.name}" style="font-weight: normal; cursor: pointer;">
                                                    ${d.name}
                                                </label>
                                            </td>
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

        // 🔍 Recherche dynamique avec maintien de la sélection
        $('#doctype-search').on('keyup', function() {
            const searchText = $(this).val().toLowerCase();

            $('#doctype-list tr').each(function() {
                const $row = $(this);
                const doctypeName = $row.text().toLowerCase();
                $row.toggle(doctypeName.includes(searchText));
            });

            // Restaurer les cases cochées après filtrage
            $('#doctype-list tr:visible .doctype-checkbox').each(function() {
                const val = $(this).val();
                $(this).prop('checked', !!selected_doctypes_map[val]);
            });

            updateSelectionCount();
        });

        $('#search-clear').click(function() {
            $('#doctype-search').val('').trigger('keyup');
        });

        // ✅ Gestion de la sélection persistante
        $(document).on('change', '.doctype-checkbox', function() {
            const name = $(this).val();
            if ($(this).is(':checked')) {
                selected_doctypes_map[name] = true;
            } else {
                delete selected_doctypes_map[name];
            }
            updateSelectionCount();
        });

        // Boutons de sélection
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
            if (selectedCount > 0) {
                $('#selected-count').removeClass('well').addClass('well-danger');
            } else {
                $('#selected-count').removeClass('well-danger').addClass('well');
            }
        }

        // 🔥 Action : suppression
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
                        method: 'erpnext.resetreini.page.pagereset.reset.reinitialiser_donnees',
                        args: { 'doctypes': selected_doctypes },
                        callback: function(r) {
                            if (r.message === 'ok') {
                                frappe.msgprint({
                                    title: __('Succès'),
                                    message: __('Données supprimées avec succès.'),
                                    indicator: 'green'
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
