frappe.pages['ops-assistant'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({ parent: wrapper, title: 'Ops Assistant', single_column: true });

	page.main.html(`
        <div class="ops-assistant">
            <div class="ops-assistant-badge text-muted small" style="margin-bottom:10px;"></div>
            <div class="ops-assistant-log" style="max-height:55vh; overflow-y:auto; margin-bottom:15px;"></div>
            <div class="form-inline">
                <input type="text" class="form-control ops-assistant-input" style="width:70%"
                    placeholder="e.g. which vehicles breached SLA this week?">
                <button class="btn btn-primary ops-assistant-ask">Ask</button>
            </div>
        </div>
    `);

	const $log = page.main.find('.ops-assistant-log');
	const $input = page.main.find('.ops-assistant-input');
	const $badge = page.main.find('.ops-assistant-badge');

	function ask() {
		const question = $input.val().trim();
		if (!question) return;
		$log.append(`<p><b>You:</b> ${frappe.utils.escape_html(question)}</p>`);
		$input.val('').prop('disabled', true);

		frappe.call({
			method: 'ksc_ops.assistant_api.ask',
			args: { question },
			freeze: true,
			callback: function (r) {
				$input.prop('disabled', false).focus();
				if (!r.message) return;
				const { answer, is_live, provider } = r.message;
				$badge.html(is_live
					? `<span class="indicator green"></span> Live LLM (${provider})`
					: `<span class="indicator orange"></span> Mock assistant (no LLM key configured)`);
				$log.append(`<div><b>Assistant:</b><br>${frappe.markdown(answer)}</div><hr>`);
				$log.scrollTop($log[0].scrollHeight);
			},
		});
	}

	page.main.find('.ops-assistant-ask').on('click', ask);
	$input.on('keypress', (e) => { if (e.which === 13) ask(); });
};
