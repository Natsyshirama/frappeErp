frappe.pages['exporter'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Export Supplier Quotations',
        single_column: true
    });

    $(page.body).html(`
        <div class="export-container" style="padding: 20px;">
            <div class="row">
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="from-date">From Date</label>
                        <input type="date" class="form-control" id="from-date">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="to-date">To Date</label>
                        <input type="date" class="form-control" id="to-date">
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="supplier">Supplier</label>
                        <input type="text" class="form-control" id="supplier" placeholder="Select Supplier">
                    </div>
                </div>
            </div>
            <div class="row" style="margin-top: 20px;">
                <div class="col-md-6">
                    <button class="btn btn-primary btn-block" id="export-csv">
                        <i class="fa fa-file-excel-o"></i> Export as CSV
                    </button>
                </div>
                <div class="col-md-6">
                    <button class="btn btn-danger btn-block" id="export-pdf">
                        <i class="fa fa-file-pdf-o"></i> Export as PDF
                    </button>
                </div>
            </div>
            <div id="progress-area" style="margin-top: 20px; display: none;">
                <div class="progress">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
                <p class="text-center" id="progress-text">Preparing export...</p>
            </div>
        </div>
    `);

    frappe.ui.form.make_control({
        parent: $('#supplier').parent(),
        df: {
            fieldtype: 'Link',
            fieldname: 'supplier',
            options: 'Supplier',
            placeholder: 'Select Supplier'
        },
        render_input: true
    });

    $('#export-csv').on('click', function() {
        export_data('CSV');
    });

    $('#export-pdf').on('click', function() {
        export_data('PDF');
    });

    function export_data(format) {
        const from_date = $('#from-date').val();
        const to_date = $('#to-date').val();
        const supplier = $('#supplier').val();

        $('#progress-area').show();
        update_progress(0, 'Starting export...');

        frappe.call({
            method: 'erpnext.export.page.exporter.exporter.export_supplier_quotations',
            args: {
                from_date: from_date,
                to_date: to_date,
                supplier: supplier,
                format: format
            },
            callback: function(r) {
                if (r.message) {
                    update_progress(100, 'Export completed!');
                    if (r.message.file_url) {
                        window.open(r.message.file_url, '_blank');
                    }
                    setTimeout(() => $('#progress-area').hide(), 2000);
                }
            },
            freeze: true,
            freeze_message: __('Exporting data...')
        });
    }

    function update_progress(percent, message) {
        $('.progress-bar').css('width', percent + '%');
        $('#progress-text').text(message);
    }
};