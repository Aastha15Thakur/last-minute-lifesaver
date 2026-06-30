'use client';

import { useState,useEffect } from 'react';

interface Subtask {
  id: number;
  task_id: number;
  title: string;
  is_completed: number;
}

interface Task {
  id: number;
  title: string;
  deadline: string;
  difficulty: string;
}

interface CoachAnalysis {
  status: 'On Track' | 'Slightly Behind' | 'High Risk';
  risk_level: 'Low' | 'Medium' | 'High';
  reason: string;
  next_focus: string;
}

interface RecoveryPlan {
  summary: string;
  today: string[];
  tomorrow: string[];
  estimated_recovery: string;
}

export default function Home() {
  const [taskInput, setTaskInput] = useState('');
  const [deadline, setDeadline] = useState('');
  const [difficulty, setDifficulty] = useState('Medium');

  const [activeTask, setActiveTask] = useState<Task | null>(null);
  const [subtasks, setSubtasks] = useState<Subtask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<CoachAnalysis | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [recoveryPlan, setRecoveryPlan] = useState<RecoveryPlan | null>(null);
  const [loadingRecovery, setLoadingRecovery] = useState(false);
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
  const timer = setTimeout(() => {
    setShowSplash(false);
  }, 1500);

  return () => clearTimeout(timer);
}, []);

  const fetchDashboard = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/dashboard');
      const data = await res.json();
      if (data.task) {
        setActiveTask(data.task);
        setSubtasks(data.subtasks);
      }
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    }
  };

  const fetchCoachAnalysis = async () => {
    setLoadingAnalysis(true);
    try {
      const res = await fetch('http://localhost:8000/api/analyze-progress');
      console.log('Status:', res.status);
      const data = await res.json();
      console.log('Coach Data:', data);
      if (res.ok) setAnalysis(data);
    } catch (error) {
      console.error('Error fetching Mission Control analysis:', error);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const fetchRecoveryPlan = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/recovery-plan');
      if (res.ok) {
        const data = await res.json();
        setRecoveryPlan(data);
      } else {
        console.error('Failed to fetch recovery plan');
      }
    } catch (error) {
      console.error('Error fetching recovery plan:', error);
    }
  };

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!taskInput.trim() || !deadline) {
      setError('Please fill in both the task and the deadline.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch('http://127.0.0.1:8000/api/generate-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_title: taskInput, deadline, difficulty }),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      await fetchDashboard();
      await Promise.all([
      fetchCoachAnalysis(),
      fetchRecoveryPlan()
      ])
  
      setTaskInput('');
    } catch (err: any) {
      setError(err.message || 'Something went wrong connecting to the backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCheck = async (id: number, currentStatus: number) => {
    const newStatus = currentStatus === 1 ? 0 : 1;
    setSubtasks(prev =>
      prev.map(sub => (sub.id === id ? { ...sub, is_completed: newStatus } : sub))
    );
    try {
      await fetch('http://127.0.0.1:8000/api/toggle-subtask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subtask_id: id, is_completed: newStatus }),
      });
      await fetchCoachAnalysis();
      await fetchRecoveryPlan();
    } catch (err) {
      console.error('Failed syncing check state to SQLite:', err);
    }
  };

  const totalSubtasks = subtasks.length;
  const completedSubtasks = subtasks.filter(s => s.is_completed === 1).length;
  const progressPercent =
    totalSubtasks > 0 ? Math.round((completedSubtasks / totalSubtasks) * 100) : 0;

  const riskColors = {
    High: {
      card: 'bg-red-50 border-red-200 text-red-900',
      badge: 'bg-red-200 text-red-800',
      focus: 'bg-red-100 border-red-300',
    },
    Medium: {
      card: 'bg-amber-50 border-amber-200 text-amber-900',
      badge: 'bg-amber-200 text-amber-800',
      focus: 'bg-amber-100 border-amber-300',
    },
    Low: {
      card: 'bg-emerald-50 border-emerald-200 text-emerald-900',
      badge: 'bg-emerald-200 text-emerald-800',
      focus: '',
    },
  };
  if (showSplash) {
  return (
    <main className="min-h-screen bg-[#060e20] flex flex-col items-center justify-center text-white">

      <img
          src="/logo.png"
          alt="Dash"
          className="w-28 h-28 mb-8 animate-pulse"
        />

      <h1 className="text-6xl font-black">
        Dash
      </h1>

      <p className="text-cyan-300 mt-2 tracking-widest uppercase">
        The Last-Minute Lifesaver
      </p>

     <p className="mt-8 text-xl font-medium text-white">
       Don't panic.
</p>

    <p className="mt-2 text-gray-400">
      I'm finding your next move...
    </p>
      <div className="w-64 h-2 bg-gray-700 rounded-full mt-8 overflow-hidden">
        <div className="h-full w-full bg-gradient-to-r from-cyan-400 via-violet-500 to-pink-500 animate-pulse" />
      </div>

    </main>
  );
}

  
return (
<>
<div className="min-h-screen bg-[#060e20] text-white">

<div className="flex">
  <aside className="hidden lg:flex w-72 min-h-screen border-r border-violet-500/20 bg-[#0b1328] flex-col p-6">

  {/* Profile */}
  <div className="glass-card rounded-2xl p-5 mb-8">

    <div className="flex items-center gap-3">

      <img
        src="/logo.png"
        className="w-12 h-12"
        alt="Dash"
      />

      <div>

        <h2 className="font-bold text-lg">
          Dash
        </h2>

        <p className="text-xs text-gray-400">
          Guest Session
        </p>

      </div>

    </div>

    <div className="mt-5 flex items-center gap-2 text-emerald-400 text-sm">

      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>

      Ready to Rescue

    </div>

  </div>

  <nav className="space-y-3">

    <button className="w-full text-left px-4 py-3 rounded-xl bg-violet-500/20">
      🏠 Dashboard
    </button>

    <button className="w-full text-left px-4 py-3 rounded-xl hover:bg-violet-500/10 transition-all duration-200">
      🎯 Mission
    </button>

    <button className="w-full text-left px-4 py-3 rounded-xl hover:bg-violet-500/10 transition-all duration-200">
      🤖 Coach
    </button>

    <button className="w-full text-left px-4 py-3 rounded-xl hover:bg-violet-500/10 transition-all duration-200">
      🚑 Recovery
    </button>

    <button className="w-full text-left px-4 py-3 rounded-xl hover:bg-violet-500/10 transition-all duration-200">
      ⚙️ Settings
    </button>

  </nav>

</aside>
<main className="flex-1 px-8 py-8">
      <div className="max-w-7xl mx-auto">
      <div className="mb-4">
  <p className="text-gray-400 text-sm">
    👋 Welcome back
  </p>

  <h1 className="text-2xl font-bold text-white mt-1">
    Dashboard
  </h1>
</div>  

        {/* Hero */}
        <div className="mb-6 rounded-3xl glass-card px-8 py-5 glow-violet">
        <div className="flex items-center justify-between gap-12">

  {/* LEFT */}

  <div className="flex items-start gap-6 flex-1">

    <img
      src="/logo.png"
      alt="Dash Logo"
      className="w-24 h-24 flex-shrink-0"
    />

    <div className="space-y-2">

      <h1 className="text-4xl md:text-5xl leading-none tracking-tight font-black text-white">
        Dash
      </h1>

      <p className="text-cyan-300 font-semibold">
        The Last-Minute Lifesaver
      </p>

      <p className="text-xl md:text-2xl leading-tight font-semibold font-semibold text-white">
        Beat deadlines. Not yourself.
      </p>

      

    </div>

  </div>

  {/* RIGHT */}

  <div className="hidden xl:flex items-start gap-4 border-l border-white/10 pl-8">

    <div className="text-violet-400 text-2xl">
      ✨
    </div>

    <div>

      <p className="font-semibold text-white">
For your last-minute plans...

      </p>

      <p className="text-gray-400 text-sm mt-2">
        
Dash is here.
      </p>

    </div>

  </div>

</div>
        </div>

        {/* Input Form */}
        <div className="glass-card glow-violet rounded-3xl p-8 flex flex-col gap-6 mb-10 border border-violet-500/20 shadow-[0_0_40px_rgba(124,58,237,0.15)]">
          <form onSubmit={handleGeneratePlan} className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <label htmlFor="task-input" className="font-semibold text-gray-300">
                What task are you procrastinating on?
              </label>
              <input
                id="task-input"
                type="text"
                disabled={loading}
                value={taskInput}
                onChange={e => setTaskInput(e.target.value)}
                placeholder="e.g., Learn Automata Theory"
               className="w-full rounded-2xl bg-[#111827] border border-violet-500/30 px-4 py-3 text-white placeholder:text-gray-500 outline-none focus:border-cyan-400 focus:shadow-[0_0_20px_rgba(34,211,238,.2)] transition-all duration-300"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="deadline-input" className="font-semibold text-gray-300">
                  Deadline
                </label>
                <input
                  id="deadline-input"
                  type="datetime-local"
                  disabled={loading}
                  value={deadline}
                  onChange={e => setDeadline(e.target.value)}
                  className="w-full rounded-xl bg-[#111827] border border-violet-500/30 px-4 py-3 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="difficulty-select" className="font-semibold text-gray-300">
                  Difficulty Level
                </label>
                <select
                  id="difficulty-select"
                  disabled={loading}
                  value={difficulty}
                  onChange={e => setDifficulty(e.target.value)}
                  className="w-full rounded-2xl bg-[#111827] border border-violet-500/30 px-4 py-3 text-white focus:outline-none focus:border-cyan-400 transition-all"
                >
                  <option value="Low">Low Priority / Easy</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High Priority / Urgent</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`py-4 rounded-xl font-bold text-lg text-white transition-all duration-300 active:scale-[0.98] ${
                loading
                  ? "bg-gradient-to-r from-slate-700 to-slate-800 cursor-not-allowed opacity-70"
                  : "bg-gradient-to-r from-violet-600 via-fuchsia-600 to-cyan-500 hover:scale-105 active:scale-95 hover:shadow-[0_0_30px_rgba(139,92,246,.45)]"
              }`}
            >
              {loading ? (
  <div className="flex items-center justify-center gap-3">
    <span className="inline-block w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
    <span>👻 Dash is planning your rescue...</span>
  </div>
) : (
  "Generate New Action Plan"
)}
            </button>
            </form>
        </div>

        {error && (
          <div className="mb-5 p-3 bg-red-50 text-red-700 rounded-lg border border-red-200 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 mb-8">

  <div className="glass-card rounded-2xl p-4 border border-violet-500/20">
    <p className="text-gray-400 text-sm flex items-center gap-2">
  📌 Active Tasks
</p>
    <h2 className="text-3xl font-bold text-white">
      {activeTask ? 1 : 0}
    </h2>
  </div>

  <div className="glass-card rounded-2xl p-5 border border-violet-500/20">
    <p className="text-gray-400 text-sm flex items-center gap-2">
  ✅ Completed
</p>
    <h2 className="text-3xl font-bold text-green-400">
      {completedSubtasks}
    </h2>
  </div>

  <div className="glass-card rounded-2xl p-5 border border-violet-500/20">
  <p className="text-gray-400 text-sm flex items-center gap-2">
  📈 Progress
</p>
    <h2 className="text-3xl font-bold text-cyan-300">
      {progressPercent}%
    </h2>
  </div>

  <div className="glass-card rounded-2xl p-5 border border-violet-500/20">
    <p className="text-gray-400 text-sm flex items-center gap-2">
  ⚡ Momentum
</p>
    <h2 className="text-3xl font-bold text-pink-400">
      {progressPercent >= 70 ? "High" : progressPercent >= 30 ? "Building" : "Starting"}
    </h2>
  </div>
</div>
<div className="glass-card rounded-3xl p-6 mb-6 border border-violet-500/20">
  <div className="flex items-center justify-between mb-4">
    <h2 className="text-2xl font-bold text-white">
      Today's Mission
    </h2>

    <span className="text-cyan-300 text-sm">
      AI Suggestion
    </span>
  </div>

  <p className="text-gray-300 leading-relaxed">
    {activeTask
      ? `Focus on "${activeTask.title}" before starting anything new. Completing your highest priority task first will give you the biggest productivity boost today.`
      : "Generate your first action plan and Dash will tell you exactly what deserves your attention today."}
  </p>
</div>
        {/* Dashboard */}
        {activeTask && (
          <div className="mt-10 space-y-6">

            {/* Momentum + Status cards */}
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="glass-card rounded-3xl p-7 border border-cyan-400/20 shadow-[0_0_35px_rgba(34,211,238,0.12)]">
                <p className="text-xs uppercase tracking-[0.35em] text-cyan-300 mb-3 font-semibold">Project Momentum</p>
                <h2 className="text-4xl font-black text-white leading-tight">{activeTask.title}</h2>
                <p className="text-gray-400 mt-2">Deadline: {activeTask.deadline.replace('T', ' ')}</p>
                <div className="mt-6">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Progress</span>
                    <span>{progressPercent}%</span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-gray-800 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-violet-500 to-pink-500 transition-all duration-700"
                      style={{ width: `${progressPercent}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="glass-card rounded-3xl p-6">
                <p className="text-sm uppercase tracking-widest text-gray-400 mb-4">Status</p>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Priority</span>
                    <span className="font-bold">{activeTask.difficulty}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Milestones</span>
                    <span className="font-bold">{completedSubtasks}/{totalSubtasks}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Completion</span>
                    <span className="font-bold">{progressPercent}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Mission Control + Recovery Mode */}
            <div className="grid lg:grid-cols-2 gap-6">
              {analysis ? (() => {
                const colors = riskColors[analysis.risk_level];
                return (
                  <div
  className={`glass-card rounded-2xl p-6 border-l-4 border-l-cyan-400 ${colors.card} shadow-[0_0_20px_rgba(34,211,238,0.08)]`}
>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">🤖</span>
                        <h3 className="font-bold text-lg tracking-wide">Mission Control</h3>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${colors.badge}`}>
                        {analysis.status}
                      </span>
                    </div>
                    <p className="text-sm opacity-90 mb-4 font-medium italic">"{analysis.reason}"</p>
                    {analysis.next_focus && analysis.status !== 'On Track' && (
                      <div className={`p-3 rounded-lg border text-sm ${colors.focus}`}>
                        <strong className="block text-xs uppercase tracking-wider opacity-75 mb-1">
                          🔥 Next High-Impact Focus:
                        </strong>
                        <span className="font-semibold">{analysis.next_focus}</span>
                      </div>
                    )}
                  </div>
                );
              })() : (
  <div className="glass-card rounded-2xl p-6 border-l-4 border-l-cyan-400">
    <div className="flex items-center gap-2 mb-3">
      <span className="text-xl">🤖</span>
      <h3 className="font-bold text-lg">Mission Control</h3>
    </div>

    <p className="text-gray-300 leading-relaxed">
      Generate your first action plan and Dash will monitor your productivity,
      identify risks, and keep you focused on the next high-impact task.
    </p>

    <div className="mt-5 text-cyan-300 text-sm">
      💡 Waiting for your first mission...
    </div>
  </div>
)}

              {recoveryPlan && (
                <div className="glass-card rounded-2xl p-6 border border-emerald-400/20 border-l-4 border-l-emerald-400">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">🚑</span>
                    <h3 className="font-bold text-lg">Recovery Mode</h3>
                  </div>
                  <p className="text-sm italic mb-4">{recoveryPlan.summary}</p>
                  <div className="mb-4">
                    <h4 className="font-semibold mb-2">📅 Today</h4>
                    <ul className="list-disc ml-6">
                      {recoveryPlan.today.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                  </div>
                  <div className="mb-4">
                    <h4 className="font-semibold mb-2">📅 Tomorrow</h4>
                    <ul className="list-disc ml-6">
                      {recoveryPlan.tomorrow.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                  </div>
                  <div className="font-semibold text-emerald-300">
                    ⏳ Estimated Recovery: {recoveryPlan.estimated_recovery}
                  </div>
                </div>
              )}
            </div>
<div className="flex items-center justify-between mb-5 mt-8">
  <div>
    <h2 className="text-2xl font-bold text-white">
      ✅ Critical Path
    </h2>
    <p className="text-sm text-gray-400 mt-1">
      Complete these milestones to finish your mission.
    </p>
  </div>

  <span className="text-sm text-cyan-300 font-medium">
    {completedSubtasks}/{totalSubtasks} Complete
  </span>
</div>
            {/* Critical Path */}
            <div className="flex flex-col gap-3">
              {subtasks.map(subtask => (
                <label
  key={subtask.id}
  className={`group flex items-center justify-between p-5 rounded-2xl transition-all duration-300 cursor-pointer border
    ${
      subtask.is_completed === 1
        ? "bg-emerald-500/10 border-emerald-400/30"
        : "glass-card border-white/10 hover:border-cyan-400/40 hover:-translate-y-1"
    }`}
>

  <div className="flex items-center gap-4">

    <input
      type="checkbox"
      checked={subtask.is_completed === 1}
      onChange={() => handleToggleCheck(subtask.id, subtask.is_completed)}
      className="w-5 h-5 accent-cyan-400 cursor-pointer"
    />

    <div>

      <p
        className={`font-semibold ${
          subtask.is_completed === 1
            ? "line-through text-gray-500"
            : "text-white"
        }`}
      >
        {subtask.title}
      </p>

      <p className="text-xs text-gray-400 mt-1">
        Mission Step
      </p>

    </div>

  </div>

  <div>

    {subtask.is_completed === 1 ? (
      <span className="text-emerald-400 font-semibold">
        ✓ Done
      </span>
    ) : (
      <span className="text-cyan-300 text-sm">
        Pending
      </span>
    )}

  </div>

</label>
              ))}
            </div>


<div className="glass-card rounded-3xl p-6 mb-8 border border-violet-500/20">
  <div className="flex items-center justify-between mb-5">
    <h2 className="text-2xl font-bold text-white">Workspace</h2>
    <span className="text-sm text-gray-400">History</span>
  </div>

  <div className="space-y-4">

    <div className="flex items-center justify-between border-b border-white/10 pb-3">
      <div>
        <p className="font-semibold text-white">
          {activeTask ? activeTask.title : "No tasks yet"}
        </p>
        <p className="text-sm text-gray-400">
          {activeTask ? activeTask.deadline.replace("T"," ") : "Generate your first action plan"}
        </p>
      </div>

      <span className="px-3 py-1 rounded-full bg-violet-500/20 text-violet-300 text-sm">
        {activeTask ? `${progressPercent}%` : "--"}
      </span>
    </div>

  </div>
</div>
          </div>
        )}

      </div>
    </main>
    </div>
    </div>
{/* Floating Dash Branding */}

<div className="fixed bottom-6 left-6 z-50 flex items-center gap-3 opacity-90 hover:opacity-100 transition-all duration-300">

  <img
    src="/logo.png"
    alt="Dash"
    className="w-11 h-11"
  />

  <div className="leading-tight">
    <h3 className="text-white font-bold text-base">
      Dash
    </h3>

    <p className="text-cyan-300 text-[11px] tracking-wide">
      The Last-Minute Lifesaver
    </p>
  </div>

</div>
    </>
  );
}
