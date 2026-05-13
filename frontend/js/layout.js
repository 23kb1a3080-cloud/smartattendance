/**
 * Shared Layout: Navbar + Sidebar
 * Injected into all pages
 */

function renderLayout(activePage) {
  const user = Auth.getUser();
  const initial = user ? (user.full_name || user.username)[0].toUpperCase() : 'U';
  const name = user ? (user.full_name || user.username) : 'User';

  const navbarHTML = `
  <nav class="navbar">
    <div class="container">
      <a href="dashboard.html" class="navbar-brand">
        <div class="logo-icon">🎓</div>
        Smart Attendance
      </a>
      <ul class="navbar-nav">
        <li><a href="dashboard.html" class="${activePage==='dashboard'?'active':''}">📊 Dashboard</a></li>
        <li><a href="students.html" class="${activePage==='students'?'active':''}">👥 Students</a></li>
        <li><a href="attendance.html" class="${activePage==='attendance'?'active':''}">📋 Attendance</a></li>
        <li><a href="reports.html" class="${activePage==='reports'?'active':''}">📈 Reports</a></li>
      </ul>
      <div class="navbar-user">
        <div class="live-dot"></div>
        <span style="font-size:0.85rem;color:var(--text-secondary)">Live</span>
        <div class="user-avatar" id="nav-user-avatar">${initial}</div>
        <span id="nav-user-name" style="font-size:0.9rem;font-weight:600">${name}</span>
        <button class="btn btn-outline btn-sm" onclick="AuthAPI.logout()">Logout</button>
      </div>
    </div>
  </nav>`;

  const sidebarHTML = `
  <aside class="sidebar">
    <div class="sidebar-section-title">Main</div>
    <ul class="sidebar-menu">
      <li><a href="dashboard.html" class="${activePage==='dashboard'?'active':''}">
        <span class="icon">📊</span> Dashboard
      </a></li>
      <li><a href="students.html" class="${activePage==='students'?'active':''}">
        <span class="icon">👥</span> Students
      </a></li>
      <li><a href="attendance.html" class="${activePage==='attendance'?'active':''}">
        <span class="icon">📋</span> Attendance
      </a></li>
      <li><a href="reports.html" class="${activePage==='reports'?'active':''}">
        <span class="icon">📈</span> Reports
      </a></li>
    </ul>
    <div class="sidebar-section-title">System</div>
    <ul class="sidebar-menu">
      <li><a href="logs.html" class="${activePage==='logs'?'active':''}">
        <span class="icon">📝</span> System Logs
      </a></li>
      <li><a href="#" onclick="AuthAPI.logout()">
        <span class="icon">🚪</span> Logout
      </a></li>
    </ul>
  </aside>`;

  document.getElementById('navbar-placeholder').innerHTML = navbarHTML;
  document.getElementById('sidebar-placeholder').innerHTML = sidebarHTML;
}
