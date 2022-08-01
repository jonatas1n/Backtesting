const formResponse = document.getElementById('form-response');
const loadingEl = document.getElementById('loading');

$('#form').ajaxForm(function(result) {
    formResponse.innerHTML = result;
    $('#main-table').DataTable({
        order: [[7, 'desc']],
        language: {
            "url": "//cdn.datatables.net/plug-ins/1.12.1/i18n/pt-BR.json"
        }
    });

    $('#fails-table').DataTable({
        language: {
            "url": "//cdn.datatables.net/plug-ins/1.12.1/i18n/pt-BR.json"
        }
    });
    formResponse.scrollIntoView();
});