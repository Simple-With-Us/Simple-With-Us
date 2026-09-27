// Public, credential-free status from the existing Better Stack page.
export function statusSummary(payload) {
  const state = payload?.data?.attributes?.aggregate_state;
  const labels = {
    operational: 'Monitored services operational',
    degraded: 'Some services have issues',
    downtime: 'Service disruption reported',
    maintenance: 'Maintenance in progress',
  };
  return Object.hasOwn(labels, state)
    ? { state, label: labels[state] }
    : { state: 'unknown', label: 'Check the status page for updates' };
}

if (typeof document !== 'undefined') {
  const label = document.querySelector('[data-service-status]');
  const checked = document.querySelector('[data-status-checked]');
  let pending = false;
  async function refresh() {
    if (!label || pending || document.hidden) return;
    pending = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch('https://status.simplewithus.com/index.json', {
        signal: controller.signal, credentials: 'omit', cache: 'no-store',
      });
      if (!response.ok) throw new Error('Status feed unavailable');
      const result = statusSummary(await response.json());
      label.textContent = result.label;
      label.dataset.state = result.state;
      checked.textContent = result.state === 'unknown' ? 'Live status unavailable here.'
        : `Checked ${new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`;
    } catch {
      label.textContent = 'Check the status page for updates';
      label.dataset.state = 'unknown';
      checked.textContent = 'Live status unavailable here.';
    } finally {
      clearTimeout(timeout);
      pending = false;
    }
  }
  refresh();
  setInterval(refresh, 60000);
  document.addEventListener('visibilitychange', refresh);
}
