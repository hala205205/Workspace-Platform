import { X } from 'lucide-react'
import type { ReactNode } from 'react'

export function Modal({ title, children, onClose, wide = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
    <section className={`modal ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true">
      <header><h2>{title}</h2><button className="icon-btn" onClick={onClose} aria-label="إغلاق"><X size={20} /></button></header>
      {children}
    </section>
  </div>
}
