"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Workspace } from "@/lib/api";

export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const router = useRouter();

  useEffect(() => {
    api.workspaces.list().then(setWorkspaces).catch(console.error);
  }, []);

  async function handleCreate() {
    if (!name || !org) return;
    setCreating(true);
    try {
      await api.workspaces.create({ name, organisation: org, created_by: "user" });
      setName(""); setOrg("");
      setShowForm(false);
      api.workspaces.list().then(setWorkspaces);
    } finally { setCreating(false); }
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Workspaces</h1>
          <p className="text-sm text-gray-500 mt-1">Each workspace tracks commitments for one team or account portfolio.</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
          <span>+</span> New Workspace
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Create workspace</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Workspace name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g. Enterprise Sales — Q3 2026"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Organisation</label>
              <input
                value={org}
                onChange={e => setOrg(e.target.value)}
                placeholder="e.g. Nexora Inc"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="text-sm text-gray-500 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors">
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={creating || !name || !org}
              className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors">
              {creating ? "Creating…" : "Create workspace"}
            </button>
          </div>
        </div>
      )}

      {/* Workspace list */}
      {workspaces.length === 0 ? (
        <div className="bg-white border border-dashed border-gray-200 rounded-xl p-16 text-center">
          <div className="text-3xl mb-3">🛡️</div>
          <div className="text-sm font-medium text-gray-700 mb-1">No workspaces yet</div>
          <div className="text-xs text-gray-400">Create one above to start tracking commitments.</div>
        </div>
      ) : (
        <div className="space-y-2">
          {workspaces.map(ws => (
            <div
              key={ws.id}
              onClick={() => router.push(`/workspace/${ws.id}`)}
              className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all group">
              <div className="flex items-center gap-4">
                <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 font-semibold text-sm">
                  {ws.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <div className="font-medium text-sm text-gray-900">{ws.name}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{ws.organisation}</div>
                </div>
              </div>
              <span className="text-gray-300 group-hover:text-blue-400 transition-colors text-lg">→</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
