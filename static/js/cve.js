function update(c) {
  cve_id = [$(c).attr('cve_id')];
  kernel_id = $(c).attr('kernel_id');
  oldStatus = parseInt($(c).attr('status_id'));
  newStatus = oldStatus == 5 ? 1 : oldStatus + 1;

  if ($(c).siblings('input').prop('checked')) {
    cve_id = $('input.cve').filter(function(idx, el) { return el.checked; })
      .map(function(idx, el) { return el.value }).get();
  }

  var spinner = spin();

  $.ajax({
    'type': 'POST',
    'url': '/update',
    'contentType': 'application/json',
    'data': JSON.stringify({
             kernel_id: kernel_id,
             status_id: newStatus,
             cve_id: cve_id.join(','),
            })
  }).done(function(data) {
    spinner.stop();
    if (data.error == "success") {
      for (var i = 0; i < cve_id.length; i++) {
        c = $('input[value="' + cve_id[i] + '"]').siblings('.status');
        $(c).attr('status_id', newStatus);
        updateCVEStatus($(c));
      }
      $("#progressbar").attr("value", data.patched);
      updateProgressBar();
    }
  });
}

function spin() {
  $('#spinner').css({'display': 'initial'});
  var target = $('#spinner')[0];
  var theSpinner = new Spinner({color: '#fff'}).spin(target);
  return {
    stop: function() {
      theSpinner.stop();
      $('#spinner').css({'display': 'none'});
    }
  }
}

function updateProgressBar() {
  $("#progressbar").progressbar({
    value: parseInt($("#progressbar").attr("value")),
  });
}

function updateCVEStatus(target) {
  status_id = target.attr('status_id');
  target.removeClass (function (index, css) {
    return (css.match (/(^|\s)status_\S+/g) || []).join(' ');
  });
  target.addClass("status_" + status_id);
  target.html($("#status_" + status_id).html());

}


function initializeCVEStatuses() {
  $.each($(".cvediv"), function(key, value) {
    updateCVEStatus($("#" + $(value).attr('id') + " .status"));
  });
}

function toggleAll(checkbox) {
  $('input').prop('checked', checkbox.checked);
}

$(document).ready(function() {
  updateProgressBar();
  initializeCVEStatuses();
});
