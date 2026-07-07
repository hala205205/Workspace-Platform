import { useEffect, useMemo, useState, type FormEvent } from 'react'
import {
  Bell, CalendarDays, Check, CheckCircle2, ChevronLeft, Clock3, FileText, Filter,
  KeyRound, LoaderCircle, MapPin, Megaphone, Pencil, Pin, Plus, Search, Send, Sparkles,
  Trash2, Users, Video, XCircle
} from 'lucide-react'
import { useAuth } from './AuthContext'
import { api, download } from './api'
import { Modal } from './components/Modal'
import { Shell, type Page } from './components/Shell'
import type { Announcement, AudienceDirectory, CommentItem, Department, EventItem, NotificationItem, Role, User } from './types'

const dateFormat = new Intl.DateTimeFormat('ar-PS', { day: 'numeric', month: 'long', year: 'numeric' })
const timeFormat = new Intl.DateTimeFormat('ar-PS', { hour: 'numeric', minute: '2-digit' })
const shortDate = new Intl.DateTimeFormat('ar-PS', { day: 'numeric', month: 'short' })
const asDate = (value: string) => new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`)
const relative = (value: string) => {
  const hours = Math.round((Date.now() - asDate(value).getTime()) / 3_600_000)
  if (hours < 1) return 'منذ قليل'
  if (hours < 24) return `منذ ${hours} ساعة`
  return dateFormat.format(asDate(value))
}

function LoginScreen() {
  const { login, bootstrap } = useAuth()
  const [setup, setSetup] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try { setup ? await bootstrap(name, email, password) : await login(email, password) }
    catch (err) { setError(err instanceof Error ? err.message : 'تعذر تسجيل الدخول') }
    finally { setBusy(false) }
  }

  return <div className="auth-page">
    <div className="auth-art"><div className="art-content"><div className="brand-mark large">W</div><p className="eyebrow">WORKSPACE</p><h1>كل ما يحتاجه فريقك<br />في مساحة واحدة.</h1><p>إعلانات واضحة، مواعيد مرتبة، وتواصل يبقي الجميع على المسار الصحيح.</p><div className="art-cards"><span><Megaphone /> إعلانات الفريق</span><span><CalendarDays /> تقويم موحّد</span><span><Bell /> تنبيهات فورية</span></div></div></div>
    <div className="auth-panel"><form className="auth-form" onSubmit={submit}>
      <div><p className="eyebrow accent">مرحباً بك</p><h2>{setup ? 'تهيئة مساحة العمل' : 'تسجيل الدخول'}</h2><p>{setup ? 'أنشئ حساب المدير الأول للبدء.' : 'أدخل بيانات حسابك للوصول إلى فريقك. عند نسيان كلمة المرور تواصل مع الأدمن.'}</p></div>
      {setup && <label>الاسم الكامل<input value={name} onChange={e => setName(e.target.value)} minLength={2} required placeholder="مثال: أحمد محمد" /></label>}
      <label>البريد الإلكتروني<input dir="ltr" type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="name@company.com" /></label>
      <label>كلمة المرور<input dir="ltr" type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={12} required placeholder="••••••••••••" /></label>
      {error && <div className="error-box"><XCircle size={18} />{error}</div>}
      <button className="primary-btn auth-submit" disabled={busy}>{busy && <LoaderCircle className="spin" size={18} />}{setup ? 'إنشاء المساحة' : 'دخول إلى مساحة العمل'}</button>
      <button type="button" className="text-btn" onClick={() => { setSetup(!setup); setError('') }}>{setup ? 'لديك حساب بالفعل؟ سجّل الدخول' : 'هذه أول مرة؟ تهيئة النظام'}</button>
    </form></div>
  </div>
}

function Header({ title, subtitle, action }: { title: string; subtitle: string; action?: React.ReactNode }) {
  return <header className="page-header"><div><p className="eyebrow">مساحة العمل</p><h1>{title}</h1><p>{subtitle}</p></div>{action}</header>
}

function Empty({ icon: Icon, title, text }: { icon: typeof Bell; title: string; text: string }) {
  return <div className="empty"><div><Icon size={28} /></div><h3>{title}</h3><p>{text}</p></div>
}

function AnnouncementCard({ item, onRefresh, canPin, canEdit, canDelete }: { item: Announcement; onRefresh: () => void; canPin: boolean; canEdit: boolean; canDelete: boolean }) {
  const [comment, setComment] = useState('')
  const [comments, setComments] = useState<CommentItem[]>([])
  const [sending, setSending] = useState(false)
  const [liked, setLiked] = useState(false)
  const [editing, setEditing] = useState(false)
  useEffect(() => {
    if (item.comments_enabled) void api<CommentItem[]>(`/announcements/${item.id}/comments`).then(setComments).catch(() => setComments([]))
  }, [item.id, item.comments_enabled])
  async function act(path: string, body?: object, method = 'POST') {
    setSending(true)
    try { await api(path, { method, body: body ? JSON.stringify(body) : undefined }); onRefresh() }
    finally { setSending(false) }
  }
  async function submitComment(e: FormEvent) {
    e.preventDefault()
    if (!comment.trim()) return
    setSending(true)
    try {
      const created = await api<CommentItem>(`/announcements/${item.id}/comments`, {
        method: 'POST', body: JSON.stringify({ content: comment.trim() })
      })
      setComments(current => [...current, created])
      setComment('')
    } finally { setSending(false) }
  }
  async function remove() {
    if (!confirm('هل تريد حذف هذا الإعلان؟')) return
    await act(`/announcements/${item.id}`, undefined, 'DELETE')
  }
  return <article className={`announcement-card ${item.is_pinned ? 'pinned' : ''}`}>
    <div className="card-meta"><span className="avatar small">إ</span><div><strong>إدارة مساحة العمل</strong><span>{relative(item.publish_at)}</span></div>{item.is_pinned && <span className="pin-label"><Pin size={14} />مثبّت</span>}</div>
    <h3>{item.title}</h3><p className="announcement-copy">{item.content}</p>
    {item.attachments.length > 0 && <div className="attachments">{item.attachments.map(file => <button key={file.id} onClick={() => void download(`/announcements/${item.id}/attachments/${file.id}`, file.original_name)}><FileText size={18} /><span>{file.original_name}<small>{Math.ceil(file.size_bytes / 1024)} KB</small></span></button>)}</div>}
    <div className="card-actions">
      <button className={liked ? 'ack-btn' : ''} disabled={sending} onClick={() => { setLiked(current => !current); void act(`/announcements/${item.id}/reactions`, { reaction_type: '👍' }) }}>👍 {liked ? 'تم الإعجاب' : 'أعجبني'}</button>
      {canPin && <button onClick={() => void act(`/announcements/${item.id}/pin`, undefined, 'PATCH')}><Pin size={16} />{item.is_pinned ? 'إلغاء التثبيت' : 'تثبيت'}</button>}
      {canEdit && <button onClick={() => setEditing(true)}><Pencil size={16} />تعديل</button>}
      {canDelete && <button onClick={() => void remove()}><Trash2 size={16} />حذف</button>}
    </div>
    {comments.length > 0 && <div className="comments-list">{comments.map(entry => <div className="comment-item" key={entry.id}><span className="avatar small">{entry.user_name.slice(0, 1)}</span><div><strong>{entry.user_name}</strong><p>{entry.content}</p><small>{relative(entry.created_at)}</small></div></div>)}</div>}
    {item.comments_enabled && <form className="comment-box" onSubmit={submitComment}>
      <input value={comment} onChange={e => setComment(e.target.value)} placeholder="اكتب تعليقاً أو سؤالاً..." /><button disabled={!comment.trim() || sending} aria-label="إرسال"><Send size={17} /></button>
    </form>}
    {editing && <AnnouncementForm initial={item} onClose={() => setEditing(false)} onCreated={() => { setEditing(false); onRefresh() }} />}
  </article>
}

function AnnouncementForm({ onClose, onCreated, initial }: { onClose: () => void; onCreated: () => void; initial?: Announcement }) {
  const [form, setForm] = useState({
    title: initial?.title || '',
    content: initial?.content || '',
    is_global: initial?.is_global ?? true,
    is_pinned: initial?.is_pinned ?? false,
    requires_acknowledgement: initial?.requires_acknowledgement ?? false,
    comments_enabled: initial?.comments_enabled ?? true,
    expires_at: initial?.expires_at ? initial.expires_at.slice(0, 16) : ''
  })
  const [directory, setDirectory] = useState<AudienceDirectory>({ users: [], roles: [], departments: [] }); const [targetType, setTargetType] = useState('DEPARTMENT'); const [targetId, setTargetId] = useState('')
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  useEffect(() => { void api<AudienceDirectory>('/directory/audiences').then(setDirectory).catch(() => undefined) }, [])
  const targetOptions = targetType === 'USER' ? directory.users : targetType === 'ROLE' ? directory.roles : directory.departments
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const payload = {
        ...form,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
        publish_at: new Date().toISOString(),
        ...(!initial || form.is_global || targetId ? { targets: form.is_global ? [] : [{ target_type: targetType, target_id: targetId }] } : {})
      }
      await api(initial ? `/announcements/${initial.id}` : '/announcements', { method: initial ? 'PATCH' : 'POST', body: JSON.stringify(payload) })
      onCreated(); onClose()
    } catch (err) { setError(err instanceof Error ? err.message : 'تعذر حفظ الإعلان') } finally { setBusy(false) }
  }
  return <Modal title={initial ? 'تعديل الإعلان' : 'إعلان جديد'} onClose={onClose} wide><form className="form-grid" onSubmit={submit}>
    <label className="full">عنوان الإعلان<input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required minLength={3} placeholder="عنوان واضح ومختصر" /></label>
    <label className="full">المحتوى<textarea value={form.content} onChange={e => setForm({ ...form, content: e.target.value })} required minLength={10} rows={6} placeholder="اكتب تفاصيل الإعلان هنا..." /></label>
    <label>تاريخ الانتهاء<input type="datetime-local" value={form.expires_at} onChange={e => setForm({ ...form, expires_at: e.target.value })} /></label>
    <label>نطاق الإعلان<select value={form.is_global ? 'global' : 'targeted'} onChange={e => setForm({ ...form, is_global: e.target.value === 'global' })}><option value="global">جميع الموظفين</option><option value="targeted">جمهور محدد</option></select></label>
    {!form.is_global && <><label>نوع الجمهور<select value={targetType} onChange={e => { setTargetType(e.target.value); setTargetId('') }}><option value="DEPARTMENT">قسم</option><option value="ROLE">دور</option><option value="USER">مستخدم</option></select></label><label>الجمهور<select required value={targetId} onChange={e => setTargetId(e.target.value)}><option value="">اختر...</option>{targetOptions.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></>}
    <div className="switches"><label><input type="checkbox" checked={form.is_pinned} onChange={e => setForm({ ...form, is_pinned: e.target.checked })} />تثبيت الإعلان</label><label><input type="checkbox" checked={form.requires_acknowledgement} onChange={e => setForm({ ...form, requires_acknowledgement: e.target.checked })} />يتطلب إقراراً</label><label><input type="checkbox" checked={form.comments_enabled} onChange={e => setForm({ ...form, comments_enabled: e.target.checked })} />السماح بالتعليقات</label></div>
    {error && <div className="error-box full">{error}</div>}<div className="modal-actions full"><button type="button" className="secondary-btn" onClick={onClose}>إلغاء</button><button className="primary-btn" disabled={busy}>{busy ? 'جارٍ الحفظ...' : initial ? 'حفظ التعديل' : 'نشر الإعلان'}</button></div>
  </form></Modal>
}

function AnnouncementsPage({ announcements, load }: { announcements: Announcement[]; load: (q?: string) => void }) {
  const { can } = useAuth(); const [query, setQuery] = useState(''); const [showForm, setShowForm] = useState(false)
  const canCreate = can('announcement.create')
  return <><Header title="الإعلانات" subtitle="تابع آخر الأخبار والتحديثات المهمة لفريقك." action={canCreate ? <button className="primary-btn" onClick={() => setShowForm(true)}><Plus size={18} />إعلان جديد</button> : undefined} />
    <div className="toolbar"><div className="search"><Search size={18} /><input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && load(query)} placeholder="ابحث في الإعلانات..." /></div><button className="secondary-btn" onClick={() => load(query)}><Filter size={17} />بحث</button></div>
    <div className="feed">{announcements.length ? announcements.map(item => <AnnouncementCard key={item.id} item={item} onRefresh={() => load(query)} canPin={can('announcement.pin')} canEdit={can('announcement.edit')} canDelete={can('announcement.delete')} />) : <Empty icon={Megaphone} title="لا توجد إعلانات" text="ستظهر إعلانات الفريق هنا عند نشرها." />}</div>
    {showForm && <AnnouncementForm onClose={() => setShowForm(false)} onCreated={() => load()} />}
  </>
}

function toLocalInput(value: string) {
  const date = asDate(value)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}T${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function EventForm({ onClose, onCreated, initial }: { onClose: () => void; onCreated: () => void; initial?: EventItem }) {
  const [form, setForm] = useState({
    title: initial?.title || '',
    description: initial?.description || '',
    start_time: initial ? toLocalInput(initial.start_time) : '',
    end_time: initial ? toLocalInput(initial.end_time) : '',
    location_type: initial?.location_type || 'ONLINE',
    meeting_link: initial?.meeting_link || '',
    physical_location: initial?.physical_location || ''
  })
  const [isGlobal, setIsGlobal] = useState(initial?.is_global ?? true); const [directory, setDirectory] = useState<AudienceDirectory>({ users: [], roles: [], departments: [] }); const [targetType, setTargetType] = useState('DEPARTMENT'); const [targetId, setTargetId] = useState('')
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  useEffect(() => { void api<AudienceDirectory>('/directory/audiences').then(setDirectory).catch(() => undefined) }, [])
  const targetOptions = targetType === 'USER' ? directory.users : targetType === 'ROLE' ? directory.roles : directory.departments
  async function submit(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      if (!form.start_time || !form.end_time) throw new Error('يرجى تحديد وقت البداية والنهاية')
      const start = new Date(form.start_time), end = new Date(form.end_time)
      if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) throw new Error('صيغة التاريخ غير صحيحة')
      const payload = {
        ...form,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        meeting_link: form.meeting_link || null,
        physical_location: form.physical_location || null,
        is_global: isGlobal,
        ...(!initial || isGlobal || targetId ? { targets: isGlobal ? [] : [{ target_type: targetType, target_id: targetId }] } : {})
      }
      await api(initial ? `/calendar/events/${initial.id}` : '/calendar/events', { method: initial ? 'PATCH' : 'POST', body: JSON.stringify(payload) }); onCreated(); onClose()
    }
    catch (err) { setError(err instanceof Error ? err.message : 'تعذر حفظ الموعد') } finally { setBusy(false) }
  }
  return <Modal title={initial ? 'تعديل الموعد' : 'موعد جديد'} onClose={onClose} wide><form className="form-grid" onSubmit={submit}>
    <label className="full">عنوان الموعد<input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required /></label>
    <label className="full">الوصف<textarea rows={3} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label>
    <label>البداية<input type="datetime-local" required value={form.start_time} onChange={e => setForm({ ...form, start_time: e.target.value })} /></label><label>النهاية<input type="datetime-local" required value={form.end_time} onChange={e => setForm({ ...form, end_time: e.target.value })} /></label>
    <label>نوع المكان<select value={form.location_type} onChange={e => setForm({ ...form, location_type: e.target.value as EventItem['location_type'] })}><option value="ONLINE">عن بُعد</option><option value="PHYSICAL">حضوري</option><option value="HYBRID">هجين</option></select></label>
    {form.location_type !== 'PHYSICAL' && <label>رابط الاجتماع<input dir="ltr" type="url" required value={form.meeting_link} onChange={e => setForm({ ...form, meeting_link: e.target.value })} placeholder="https://..." /></label>}
    {form.location_type !== 'ONLINE' && <label>الموقع<input value={form.physical_location} required onChange={e => setForm({ ...form, physical_location: e.target.value })} /></label>}
    <label>نطاق الموعد<select value={isGlobal ? 'global' : 'targeted'} onChange={e => setIsGlobal(e.target.value === 'global')}><option value="global">جميع الموظفين</option><option value="targeted">جمهور محدد</option></select></label>
    {!isGlobal && <><label>نوع الجمهور<select value={targetType} onChange={e => { setTargetType(e.target.value); setTargetId('') }}><option value="DEPARTMENT">قسم</option><option value="ROLE">دور</option><option value="USER">مستخدم</option></select></label><label>الجمهور<select required value={targetId} onChange={e => setTargetId(e.target.value)}><option value="">اختر...</option>{targetOptions.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></>}
    {error && <div className="error-box full">{error}</div>}<div className="modal-actions full"><button type="button" className="secondary-btn" onClick={onClose}>إلغاء</button><button className="primary-btn" disabled={busy}>{initial ? 'حفظ التعديل' : 'حفظ الموعد'}</button></div>
  </form></Modal>
}

function CalendarPage({ events, load }: { events: EventItem[]; load: (layer?: string) => void }) {
  const { can } = useAuth(); const [layer, setLayer] = useState(''); const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<EventItem | null>(null)
  const [rsvpStatus, setRsvpStatus] = useState<Record<string, string>>({})
  const grouped = useMemo(() => events.reduce<Record<string, EventItem[]>>((acc, event) => { const key = dateFormat.format(asDate(event.start_time)); (acc[key] ||= []).push(event); return acc }, {}), [events])
  async function rsvp(id: string, status: string) { await api(`/calendar/events/${id}/rsvp`, { method: 'POST', body: JSON.stringify({ status }) }); setRsvpStatus(current => ({ ...current, [id]: status })); load(layer) }
  async function remind(id: string) { await api(`/calendar/events/${id}/reminder`, { method: 'PUT', body: JSON.stringify({ minutes_before: 60 }) }); alert('تم ضبط التذكير قبل الموعد بساعة') }
  async function remove(id: string) { if (!confirm('هل تريد حذف هذا الموعد؟')) return; await api(`/calendar/events/${id}`, { method: 'DELETE' }); load(layer) }
  return <><Header title="التقويم" subtitle="كل مواعيدك واجتماعات فريقك في مكان واحد." action={can('event.create') ? <button className="primary-btn" onClick={() => setShowForm(true)}><Plus size={18} />موعد جديد</button> : undefined} />
    <div className="calendar-tabs">{[['', 'الكل'], ['TEAM', 'القسم'], ['MINE', 'تقويمي']].map(([id, label]) => <button className={layer === id ? 'active' : ''} onClick={() => { setLayer(id); load(id) }} key={id}>{label}</button>)}</div>
    <div className="agenda">{Object.keys(grouped).length ? Object.entries(grouped).map(([date, list]) => <section key={date}><h3>{date}</h3>{list.map(event => <article className="event-card" key={event.id}><div className="event-time"><strong>{timeFormat.format(asDate(event.start_time))}</strong><span>{timeFormat.format(asDate(event.end_time))}</span></div><div className="event-line" /><div className="event-body"><span className={`event-type ${event.location_type.toLowerCase()}`}>{event.location_type === 'ONLINE' ? 'عن بُعد' : event.location_type === 'PHYSICAL' ? 'حضوري' : 'هجين'}</span><h4>{event.title}</h4><p>{event.description}</p><div className="event-details">{event.meeting_link && <a href={event.meeting_link} target="_blank"><Video size={15} />رابط الاجتماع</a>}{event.physical_location && <span><MapPin size={15} />{event.physical_location}</span>}{rsvpStatus[event.id] && <span className="status success">{rsvpStatus[event.id] === 'ACCEPTED' ? 'سأحضر' : 'ربما'}</span>}</div><div className="event-actions"><button onClick={() => void rsvp(event.id, 'ACCEPTED')}><Check size={15} />سأحضر</button><button onClick={() => void rsvp(event.id, 'TENTATIVE')}>ربما</button><button onClick={() => void remind(event.id)}><Bell size={15} />ذكّرني</button>{can('event.edit') && <button onClick={() => setEditing(event)}><Pencil size={15} />تعديل</button>}{can('event.delete') && <button onClick={() => void remove(event.id)}><Trash2 size={15} />حذف</button>}</div></div></article>)}</section>) : <Empty icon={CalendarDays} title="لا توجد مواعيد" text="ستظهر المواعيد والاجتماعات القادمة هنا." />}</div>
    {showForm && <EventForm onClose={() => setShowForm(false)} onCreated={() => load(layer)} />}
    {editing && <EventForm initial={editing} onClose={() => setEditing(null)} onCreated={() => { setEditing(null); load(layer) }} />}
  </>
}

function NotificationsPage({ items, load }: { items: NotificationItem[]; load: () => void }) {
  async function read(id: string) { await api(`/notifications/${id}/read`, { method: 'PATCH' }); load() }
  async function all() { await api('/notifications/read-all', { method: 'PATCH' }); load() }
  return <><Header title="الإشعارات" subtitle="ابقَ على اطلاع بكل ما يهمك." action={items.some(x => !x.is_read) ? <button className="secondary-btn" onClick={() => void all()}><Check size={17} />تحديد الكل كمقروء</button> : undefined} />
    <div className="notification-list">{items.length ? items.map(item => <button key={item.id} className={`notification-row ${!item.is_read ? 'unread' : ''}`} onClick={() => !item.is_read && void read(item.id)}><div className="notification-icon">{item.kind.includes('event') ? <CalendarDays /> : <Megaphone />}</div><div><strong>{item.title}</strong><p>{item.body}</p><span>{relative(item.created_at)}</span></div>{!item.is_read && <i />}</button>) : <Empty icon={Bell} title="صندوقك هادئ" text="لا توجد إشعارات جديدة الآن." />}</div>
  </>
}

function AdminPage() {
  const [users, setUsers] = useState<User[]>([]); const [roles, setRoles] = useState<Role[]>([]); const [departments, setDepartments] = useState<Department[]>([]); const [show, setShow] = useState<'user' | 'role' | 'department' | null>(null); const [resetUser, setResetUser] = useState<User | null>(null)
  async function load() { const [u, r, d] = await Promise.all([api<User[]>('/admin/users'), api<Role[]>('/admin/roles'), api<Department[]>('/admin/departments')]); setUsers(u); setRoles(r); setDepartments(d) }
  useEffect(() => { void load() }, [])
  return <><Header title="إدارة الفريق" subtitle="المستخدمون والأدوار والأقسام في مؤسستك." action={<div className="header-actions"><button className="secondary-btn" onClick={() => setShow('department')}><Plus size={17} />قسم جديد</button><button className="secondary-btn" onClick={() => setShow('role')}><Plus size={17} />دور جديد</button><button className="primary-btn" onClick={() => setShow('user')}><Plus size={18} />مستخدم جديد</button></div>} />
    <div className="stats-grid compact"><div><Users /><span>المستخدمون<strong>{users.length}</strong></span></div><div><Sparkles /><span>الأدوار<strong>{roles.length}</strong></span></div><div><MapPin /><span>الأقسام<strong>{departments.length}</strong></span></div></div>
    <div className="table-card"><table><thead><tr><th>المستخدم</th><th>الدور</th><th>الحالة</th><th>تاريخ الانضمام</th><th>إجراءات</th></tr></thead><tbody>{users.map(user => <tr key={user.id}><td><div className="person"><span className="avatar small">{user.name[0]}</span><div><strong>{user.name}</strong><span>{user.email}</span></div></div></td><td>{user.role_name}</td><td><span className={`status ${user.is_active ? 'success' : 'muted'}`}>{user.is_active ? 'نشط' : 'موقوف'}</span></td><td>{shortDate.format(asDate(user.created_at))}</td><td><button className="table-action" onClick={() => setResetUser(user)}><KeyRound size={15} />تعيين كلمة مرور</button></td></tr>)}</tbody></table></div>
    {show === 'user' && <UserForm roles={roles} departments={departments} onClose={() => setShow(null)} onCreated={() => { setShow(null); void load() }} />}
    {show === 'role' && <RoleForm onClose={() => setShow(null)} onCreated={() => { setShow(null); void load() }} />}
    {show === 'department' && <DepartmentForm departments={departments} onClose={() => setShow(null)} onCreated={() => { setShow(null); void load() }} />}
    {resetUser && <ResetPasswordForm user={resetUser} onClose={() => setResetUser(null)} onDone={() => setResetUser(null)} />}
  </>
}

function UserForm({ roles, departments, onClose, onCreated }: { roles: Role[]; departments: Department[]; onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({ name: '', email: '', password: '', role_id: roles[0]?.id || '', department_id: '' }); const [error, setError] = useState('')
  async function submit(e: FormEvent) { e.preventDefault(); try { await api('/admin/users', { method: 'POST', body: JSON.stringify({ ...form, department_id: form.department_id || null }) }); onCreated() } catch (err) { setError(err instanceof Error ? err.message : 'تعذر إنشاء المستخدم') } }
  return <Modal title="إضافة مستخدم" onClose={onClose}><form className="form-grid" onSubmit={submit}><label className="full">الاسم<input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label><label className="full">البريد<input dir="ltr" type="email" required value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /></label><label className="full">كلمة مرور مؤقتة<input dir="ltr" type="password" minLength={12} required value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /></label><label>الدور<select required value={form.role_id} onChange={e => setForm({ ...form, role_id: e.target.value })}>{roles.map(r => <option value={r.id} key={r.id}>{r.name}</option>)}</select></label><label>القسم<select value={form.department_id} onChange={e => setForm({ ...form, department_id: e.target.value })}><option value="">بدون قسم</option>{departments.map(d => <option value={d.id} key={d.id}>{d.name}</option>)}</select></label>{error && <div className="error-box full">{error}</div>}<div className="modal-actions full"><button type="button" className="secondary-btn" onClick={onClose}>إلغاء</button><button className="primary-btn">إضافة المستخدم</button></div></form></Modal>
}

function ResetPasswordForm({ user, onClose, onDone }: { user: User; onClose: () => void; onDone: () => void }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  async function submit(e: FormEvent) {
    e.preventDefault(); setError('')
    try {
      await api(`/admin/users/${user.id}/reset-password`, { method: 'POST', body: JSON.stringify({ new_password: password }) })
      setDone(true); setPassword('')
    } catch (err) { setError(err instanceof Error ? err.message : 'تعذر تعيين كلمة المرور') }
  }
  return <Modal title={`تعيين كلمة مرور لـ ${user.name}`} onClose={done ? onDone : onClose}><form className="form-grid" onSubmit={submit}><p className="full">اكتب كلمة مرور مؤقتة وأخبر المستخدم بها ليتمكن من تسجيل الدخول ثم تغييرها من الإعدادات.</p><label className="full">كلمة المرور المؤقتة<input dir="ltr" type="password" minLength={12} required value={password} onChange={e => setPassword(e.target.value)} /></label>{done && <div className="success-box full"><CheckCircle2 size={18} />تم تعيين كلمة المرور بنجاح.</div>}{error && <div className="error-box full">{error}</div>}<div className="modal-actions full"><button type="button" className="secondary-btn" onClick={done ? onDone : onClose}>إغلاق</button><button className="primary-btn" disabled={done}>تعيين كلمة المرور</button></div></form></Modal>
}

const permissionOptions = [
  ['announcement.create', 'إنشاء الإعلانات'], ['announcement.edit', 'تعديل الإعلانات'],
  ['announcement.delete', 'حذف الإعلانات'], ['announcement.pin', 'تثبيت الإعلانات'],
  ['announcement.report', 'تقارير القراءة'], ['event.create', 'إنشاء المواعيد'],
  ['event.edit', 'تعديل المواعيد'], ['event.delete', 'حذف المواعيد'],
  ['user.manage', 'إدارة المستخدمين'], ['role.manage', 'إدارة الأدوار'],
]

function RoleForm({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState(''); const [description, setDescription] = useState(''); const [permissions, setPermissions] = useState<string[]>([]); const [error, setError] = useState('')
  function toggle(permission: string) { setPermissions(current => current.includes(permission) ? current.filter(item => item !== permission) : [...current, permission]) }
  async function submit(e: FormEvent) { e.preventDefault(); try { await api('/admin/roles', { method: 'POST', body: JSON.stringify({ name, description: description || null, permission_keys: permissions }) }); onCreated() } catch (err) { setError(err instanceof Error ? err.message : 'تعذر إنشاء الدور') } }
  return <Modal title="إضافة دور جديد" onClose={onClose} wide><form className="form-grid" onSubmit={submit}><label>اسم الدور<input required minLength={2} value={name} onChange={e => setName(e.target.value)} placeholder="مثال: مدير فريق" /></label><label>الوصف<input value={description} onChange={e => setDescription(e.target.value)} placeholder="وصف مختصر لمسؤوليات الدور" /></label><div className="full permission-box"><strong>الصلاحيات</strong><div>{permissionOptions.map(([key, label]) => <label key={key}><input type="checkbox" checked={permissions.includes(key)} onChange={() => toggle(key)} />{label}</label>)}</div></div>{error && <div className="error-box full">{error}</div>}<div className="modal-actions full"><button type="button" className="secondary-btn" onClick={onClose}>إلغاء</button><button className="primary-btn">إنشاء الدور</button></div></form></Modal>
}

function DepartmentForm({ departments, onClose, onCreated }: { departments: Department[]; onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState(''); const [parentId, setParentId] = useState(''); const [error, setError] = useState('')
  async function submit(e: FormEvent) { e.preventDefault(); try { await api('/admin/departments', { method: 'POST', body: JSON.stringify({ name, parent_id: parentId || null }) }); onCreated() } catch (err) { setError(err instanceof Error ? err.message : 'تعذر إنشاء القسم') } }
  return <Modal title="إضافة قسم جديد" onClose={onClose}><form className="form-grid" onSubmit={submit}><label className="full">اسم القسم<input required minLength={2} value={name} onChange={e => setName(e.target.value)} placeholder="مثال: الموارد البشرية" /></label><label className="full">القسم الرئيسي<select value={parentId} onChange={e => setParentId(e.target.value)}><option value="">قسم رئيسي</option>{departments.map(department => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label>{error && <div className="error-box full">{error}</div>}<div className="modal-actions full"><button type="button" className="secondary-btn" onClick={onClose}>إلغاء</button><button className="primary-btn">إنشاء القسم</button></div></form></Modal>
}

function SettingsPage() {
  const { user, refreshUser, logout } = useAuth()
  const [name, setName] = useState(user?.name || '')
  const [notificationsEnabled, setNotificationsEnabled] = useState(user?.notifications_enabled ?? true)
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '' })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function saveProfile(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(''); setMessage('')
    try {
      await api('/auth/me', { method: 'PATCH', body: JSON.stringify({ name, notifications_enabled: notificationsEnabled }) })
      await refreshUser()
      setMessage('تم حفظ الإعدادات بنجاح.')
    } catch (err) { setError(err instanceof Error ? err.message : 'تعذر حفظ الإعدادات') }
    finally { setBusy(false) }
  }

  async function changePassword(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError(''); setMessage('')
    try {
      await api('/auth/change-password', { method: 'POST', body: JSON.stringify(passwords) })
      setMessage('تم تغيير كلمة المرور. يرجى تسجيل الدخول مرة أخرى.')
      setPasswords({ current_password: '', new_password: '' })
      window.setTimeout(() => void logout(), 900)
    } catch (err) { setError(err instanceof Error ? err.message : 'تعذر تغيير كلمة المرور') }
    finally { setBusy(false) }
  }

  return <><Header title="الإعدادات" subtitle="حدّث بيانات حسابك وتفضيلاتك الأمنية." />
    <div className="settings-grid">
      <form className="settings-card" onSubmit={saveProfile}>
        <h2>الملف الشخصي</h2>
        <label>الاسم الكامل<input value={name} onChange={e => setName(e.target.value)} minLength={2} required /></label>
        <label className="check-row"><input type="checkbox" checked={notificationsEnabled} onChange={e => setNotificationsEnabled(e.target.checked)} /> تفعيل الإشعارات</label>
        <button className="primary-btn" disabled={busy}>حفظ الإعدادات</button>
      </form>
      <form className="settings-card" onSubmit={changePassword}>
        <h2>تغيير كلمة المرور</h2>
        <label>كلمة المرور الحالية<input dir="ltr" type="password" minLength={12} required value={passwords.current_password} onChange={e => setPasswords({ ...passwords, current_password: e.target.value })} /></label>
        <label>كلمة المرور الجديدة<input dir="ltr" type="password" minLength={12} required value={passwords.new_password} onChange={e => setPasswords({ ...passwords, new_password: e.target.value })} /></label>
        <button className="secondary-btn" disabled={busy}>تغيير كلمة المرور</button>
      </form>
    </div>
    {message && <div className="success-box floating"><CheckCircle2 size={18} />{message}</div>}
    {error && <div className="error-box floating"><XCircle size={18} />{error}</div>}
  </>
}

function HomePage({ announcements, events, notifications, setPage }: { announcements: Announcement[]; events: EventItem[]; notifications: NotificationItem[]; setPage: (p: Page) => void }) {
  const { user } = useAuth(); const upcoming = events.filter(e => asDate(e.end_time) > new Date()).slice(0, 3); const unread = notifications.filter(n => !n.is_read).length
  return <><Header title={`أهلاً، ${user?.name.split(' ')[0] || ''}`} subtitle="إليك ملخص ما يحدث في مساحة عملك اليوم." />
    <div className="stats-grid"><div><Megaphone /><span>إعلانات جديدة<strong>{announcements.length}</strong></span></div><div><CalendarDays /><span>مواعيد قادمة<strong>{upcoming.length}</strong></span></div><div><Bell /><span>إشعارات غير مقروءة<strong>{unread}</strong></span></div></div>
    <div className="dashboard-grid"><section className="panel"><div className="panel-title"><div><p className="eyebrow">آخر التحديثات</p><h2>الإعلانات</h2></div><button onClick={() => setPage('announcements')}>عرض الكل<ChevronLeft size={17} /></button></div>{announcements.slice(0, 3).map(a => <div className="mini-announcement" key={a.id}><span className="avatar small">إ</span><div><strong>{a.title}</strong><p>{a.content}</p><small>{relative(a.publish_at)}</small></div>{a.is_pinned && <Pin size={16} />}</div>)}{!announcements.length && <Empty icon={Megaphone} title="لا تحديثات" text="لا توجد إعلانات منشورة." />}</section>
      <section className="panel"><div className="panel-title"><div><p className="eyebrow">جدولك</p><h2>القادم</h2></div><button onClick={() => setPage('calendar')}>فتح التقويم<ChevronLeft size={17} /></button></div>{upcoming.map(e => <div className="mini-event" key={e.id}><div className="date-block"><strong>{asDate(e.start_time).getDate()}</strong><span>{shortDate.format(asDate(e.start_time)).split(' ')[1]}</span></div><div><strong>{e.title}</strong><span><Clock3 size={14} />{timeFormat.format(asDate(e.start_time))}</span></div></div>)}{!upcoming.length && <Empty icon={CalendarDays} title="يوم هادئ" text="لا توجد مواعيد قادمة." />}</section></div>
  </>
}

export default function App() {
  const { user, loading } = useAuth(); const [page, setPage] = useState<Page>('home')
  const [announcements, setAnnouncements] = useState<Announcement[]>([]); const [events, setEvents] = useState<EventItem[]>([]); const [notifications, setNotifications] = useState<NotificationItem[]>([]); const [error, setError] = useState('')
  async function loadAnnouncements(q = '') { try { setAnnouncements(await api(`/announcements${q ? `?q=${encodeURIComponent(q)}` : ''}`)) } catch (e) { setError((e as Error).message) } }
  async function loadEvents(layer = '') { try { setEvents(await api(`/calendar/events${layer ? `?layer=${layer}` : ''}`)) } catch (e) { setError((e as Error).message) } }
  async function loadNotifications() { try { setNotifications(await api('/notifications')) } catch (e) { setError((e as Error).message) } }
  useEffect(() => { if (user) { void loadAnnouncements(); void loadEvents(); void loadNotifications() } }, [user])
  if (loading) return <div className="splash"><div className="brand-mark large">W</div><LoaderCircle className="spin" /></div>
  if (!user) return <LoginScreen />
  const content = page === 'home' ? <HomePage announcements={announcements} events={events} notifications={notifications} setPage={setPage} /> : page === 'announcements' ? <AnnouncementsPage announcements={announcements} load={loadAnnouncements} /> : page === 'calendar' ? <CalendarPage events={events} load={loadEvents} /> : page === 'notifications' ? <NotificationsPage items={notifications} load={loadNotifications} /> : page === 'settings' ? <SettingsPage /> : <AdminPage />
  return <Shell page={page} setPage={setPage} unread={notifications.filter(n => !n.is_read).length}>{error && <button className="global-error" onClick={() => setError('')}>{error}<XCircle size={17} /></button>}{content}</Shell>
}
