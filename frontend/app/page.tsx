"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Workspace } from "@/lib/api";

export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [creating, setCreating] = useState(false);
  const router = useRouter();

  useEffect(() => { api.workspaces.list().then(setWorkspaces).catch(console.error); }, []);

  async function handleCreate() {
    if (!name || !org) return;
    setCreating(true);
    try {
      await api.workspaces.create({ name, organisation: org, created_by: "user" });
      setName(""); setOrg("");
      api.workspaces.list().then(setWorkspaces);
    } finally { setCreating(false); }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold mb-1">Workspaces</h1>
        <p className="text-gray-500 text-sm">Each workspace monitors commitments for one team or product.</p>
      </div>

      {/* Create workspace */}
      <div className="bg-white border border-gray-200 rounded-lg p-5 mb-8 flex gap-3 items-end">
        <div className="flex-1">
          <label className="block text-xs font-medium text-gray-600 mb-1">Workspace name</label>
          <input value={name} onChange={e => setName(e.target.value)}
            placeholder="e.g. Enterprise Sales — Q3 2026"
            className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div className="flex-1">
          <label className="block text-xs font-medium text-gray-600 mb-1">Organisation</label>
          <input value={org} onChange={e => setOrg(e.target.value)}
            placeholder="e.g. Nexora Inc"
            className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <button onClick={handleCreate} disabled={creating || !name || !org}
          className="bg-blue-600 text-white text-sm px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-40">
          {creating ? "Creating…" : "New Workspace"}
        </button>
      </div>

      {/* Workspace list */}
      <div className="space-y-3">
        {workspaces.length === 0 && (
          <div className="text-gray-400 text-sm py-8 text-center">No workspaces yet. Create one above.</div>
        )}
        {workspaces.map(ws => (
          <div key={ws.id} onClick={() => router.push(`/workspace/${ws.id}`)}
            className="bg-white border border-gray-200 rounded-lg px-5 py-4 flex items-center justify-between cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all">
            <div>
              <div className="font-medium text-sm">{ws.name}</div>
              <div className="text-xs text-gray-400 mt-0.5">{ws.organisation}</div>
            </div>
            <span className="text-gray-300 text-lg">→</span>
          </div>
        ))}
      </div>
    </div>
  );
}
