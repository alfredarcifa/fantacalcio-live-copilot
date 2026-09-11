import { createContext, useContext } from "react";
const SelectContext = createContext(null);
export function Select({ value, onValueChange, children }) { return <SelectContext.Provider value={{value,onValueChange}}>{children}</SelectContext.Provider>; }
export function SelectTrigger({ className="", children }) { return <div className={className}>{children}</div>; }
export function SelectValue() { return null; }
export function SelectContent({ children }) { const ctx=useContext(SelectContext); return <select value={ctx.value} onChange={e=>ctx.onValueChange(e.target.value)} className="w-full rounded-xl border border-slate-700 bg-slate-950 px-2 py-2">{children}</select>; }
export function SelectItem({ value, children }) { return <option value={value}>{children}</option>; }