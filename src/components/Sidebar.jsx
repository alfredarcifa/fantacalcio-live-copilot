const items = [["dashboard","⌂","Dashboard"],["all","▦","Listone"],["mine","★","Lista 25"],["auction","⚡","Asta live"],["managers","◎","Fantallenatori"],["stats","↗","Statistiche"]];
export default function Sidebar({ tab, setTab, reset }) {
  return <aside className="sticky top-0 z-30 flex h-16 w-full overflow-x-auto border-b border-app-line bg-app-rail md:h-screen md:w-[86px] md:flex-col md:border-b-0 md:border-r">
    <div className="grid h-16 w-16 shrink-0 place-items-center bg-app-accent text-xl font-black text-black md:h-[86px] md:w-[86px]">FC</div>
    {items.map(([id,icon,label]) => <button key={id} title={label} onClick={() => setTab(id)} className={`flex h-16 min-w-16 flex-col items-center justify-center gap-1 border-b-2 text-xs transition md:h-[74px] md:w-[86px] md:border-b-0 md:border-l-2 ${tab === id ? "border-app-accent bg-white/5 text-app-accent" : "border-transparent text-app-muted hover:bg-white/5 hover:text-white"}`}><b className="text-xl">{icon}</b><small className="hidden text-[9px] md:block">{label}</small></button>)}
    <button onClick={reset} title="Reset asta" className="ml-auto flex h-16 min-w-16 flex-col items-center justify-center text-app-muted hover:text-app-danger md:mt-auto md:ml-0 md:h-[74px] md:w-[86px]"><b className="text-xl">↻</b><small className="hidden text-[9px] md:block">Reset</small></button>
  </aside>;
}
