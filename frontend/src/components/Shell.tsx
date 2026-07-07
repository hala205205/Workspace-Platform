import { Bell, CalendarDays, ChevronLeft, LayoutDashboard, LogOut, Megaphone, Settings, Users } from 'lucide-react'
import type { ReactNode } from 'react'
import { useAuth } from '../AuthContext'

export type Page = 'home' | 'announcements' | 'calendar' | 'notifications' | 'admin' | 'settings'

const items = [
  { id: 'home', label: 'نظرة عامة', icon: LayoutDashboard },
  { id: 'announcements', label: 'الإعلانات', icon: Megaphone },
  { id: 'calendar', label: 'التقويم', icon: CalendarDays },
  { id: 'notifications', label: 'الإشعارات', icon: Bell },
] as const

export function Shell({ page, setPage, children, unread }: { page: Page; setPage: (p: Page) => void; children: ReactNode; unread: number }) {
  const { user, logout, can } = useAuth()
  const admin = can('user.manage') || can('role.manage')
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">W</div><div><strong>مساحة العمل</strong><span>بوابتك الداخلية</span></div></div>
      <nav>
        {items.map(item => <button key={item.id} className={page === item.id ? 'active' : ''} onClick={() => setPage(item.id)}>
          <item.icon size={20} /><span>{item.label}</span>{item.id === 'notifications' && unread > 0 && <b className="nav-badge">{unread}</b>}
        </button>)}
        {admin && <button className={page === 'admin' ? 'active' : ''} onClick={() => setPage('admin')}><Users size={20} /><span>الإدارة</span></button>}
      </nav>
      <div className="sidebar-foot">
        <button className={page === 'settings' ? 'active' : ''} onClick={() => setPage('settings')}><Settings size={19} /><span>الإعدادات</span></button>
        <button onClick={() => void logout()}><LogOut size={19} /><span>تسجيل الخروج</span></button>
        <div className="user-card"><div className="avatar">{user?.name.slice(0, 1)}</div><div><strong>{user?.name}</strong><span>{user?.role_name || 'مستخدم'}</span></div><ChevronLeft size={17} /></div>
      </div>
    </aside>
    <main className="main-content">{children}</main>
  </div>
}
