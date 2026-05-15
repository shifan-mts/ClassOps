import React, { useState, useEffect } from 'react';

const MODULES = [
  "overview", "attendance", "meet", "ai-tools", 
  "evaluations", "timetable", "student-dashboard", "admin_settings"
];
const PERMISSIONS = ["access", "view", "edit", "manage"];

const PERMISSION_DETAILS = {
  access: "Allows members to open and enter the section from the sidebar.",
  view: "Allows members to see data, reports, and existing records within this module.",
  edit: "Allows members to create new content and update existing entries.",
  manage: "Allows members to delete data or change administrative settings and configurations."
};

const MODULE_TITLES = {
  overview: "General Overview",
  attendance: "Attendance Management",
  meet: "Class Meetings",
  "ai-tools": "AI Assistant & Tools",
  evaluations: "Student Evaluations",
  timetable: "Class Timetable",
  "student-dashboard": "Student Portal",
  admin_settings: "System Administration"
};

const DEFAULT_ROLE_COLORS = {
  admin: "#ed4245",
  teacher: "#faa61a",
  student: "#3ba55c",
  demo: "#5865f2",
  visitor: "#9b59b6"
};

const getLightBg = (hex) => {
  if (!hex) return "#f2f3f5";
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, 0.12)`;
};

export default function AdminPanel({ API_BASE }) {
  const [roles, setRoles] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Role Editor State
  const [editingRole, setEditingRole] = useState(null);
  const [roleName, setRoleName] = useState("");
  const [roleColor, setRoleColor] = useState("#7289da");
  const [roleDefaultDuration, setRoleDefaultDuration] = useState(""); // Default duration for this role
  const [rolePerms, setRolePerms] = useState({});
  const [activeEditorTab, setActiveEditorTab] = useState("permissions");
  const [permSearch, setPermSearch] = useState("");
  const [newMemberEmail, setNewMemberEmail] = useState("");
  const [newMemberDuration, setNewMemberDuration] = useState("");

  // Member Management State
  const [assignEmails, setAssignEmails] = useState("");
  const [assignRole, setAssignRole] = useState("");
  const [assignDuration, setAssignDuration] = useState("");
  const [selectedEmails, setSelectedEmails] = useState([]);
  const [memberSearch, setMemberSearch] = useState("");
  const [isAddingMember, setIsAddingMember] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resRoles, resAssig] = await Promise.all([
        fetch(`${API_BASE}/api/roles`, { credentials: "include" }),
        fetch(`${API_BASE}/api/role-assignments`, { credentials: "include" })
      ]);
      if (resRoles.ok) setRoles(await resRoles.json());
      if (resAssig.ok) setAssignments(await resAssig.json());
    } catch (err) {
      console.error("Failed to fetch admin data", err);
    }
    setLoading(false);
    setSelectedEmails([]);
  };

  const getAvatarInfo = (email) => {
    const name = email.split('@')[0];
    const initial = name.charAt(0).toUpperCase();
    let hash = 0;
    for (let i = 0; i < email.length; i++) {
      hash = email.charCodeAt(i) + ((hash << 5) - hash);
    }
    const color = `hsl(${Math.abs(hash % 360)}, 65%, 40%)`;
    return { initial, color, displayName: name };
  };

  const handleEditRole = (role) => {
    setEditingRole(role);
    setRoleName(role.name);
    setRoleColor(role.color || DEFAULT_ROLE_COLORS[role.name.toLowerCase()] || "#7289da");
    setRoleDefaultDuration(role.default_duration || "");
    setRolePerms(role.permissions || {});
    setActiveEditorTab("permissions");
    setNewMemberEmail("");
    setNewMemberDuration(role.default_duration || "");
    setPermSearch("");
  };

  const handleCreateNewRole = () => {
    setEditingRole({ isNew: true });
    setRoleName("");
    setRoleColor("#7289da");
    setRoleDefaultDuration("");
    setRolePerms({});
    setActiveEditorTab("display");
    setNewMemberDuration("");
  };

  const togglePermission = (mod, perm) => {
    setRolePerms(prev => {
      const modPerms = prev[mod] ? [...prev[mod]] : [];
      if (modPerms.includes(perm)) {
        return { ...prev, [mod]: modPerms.filter(p => p !== perm) };
      } else {
        return { ...prev, [mod]: [...modPerms, perm] };
      }
    });
  };

  const handleGrantAll = () => {
    const allPerms = {};
    MODULES.forEach(mod => { allPerms[mod] = [...PERMISSIONS]; });
    setRolePerms(allPerms);
  };

  const handleClearAll = () => { setRolePerms({}); };

  const saveRole = async () => {
    if (!roleName.trim()) return alert("Role name is required");
    const method = editingRole.isNew ? "POST" : "PUT";
    const url = editingRole.isNew ? `${API_BASE}/api/roles` : `${API_BASE}/api/roles/${editingRole.name}`;
    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ 
          name: roleName.trim(), 
          permissions: rolePerms, 
          color: roleColor,
          default_duration: roleDefaultDuration
        })
      });
      if (res.ok) { setEditingRole(null); fetchData(); }
      else { alert((await res.json()).error || "Failed to save role"); }
    } catch (err) { alert("Error saving role"); }
  };

  const deleteRole = async (name) => {
    if (!confirm(`Are you sure you want to delete role '${name}'?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/roles/${name}`, { method: "DELETE", credentials: "include" });
      if (res.ok) fetchData();
      else alert((await res.json()).error);
    } catch (err) { alert("Error deleting role"); }
  };

  const handleUpdateMemberRole = async (email, role, duration = "") => {
    try {
      const res = await fetch(`${API_BASE}/api/role-assignments`, {
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
        body: JSON.stringify({ emails: [email], role, duration_hrs: duration })
      });
      if (res.ok) fetchData();
      else alert((await res.json()).error);
    } catch (err) { alert("Failed to update role"); }
  };

  const saveAssignments = async () => {
    if (!assignEmails.trim() || !assignRole) return alert("Emails and role are required");
    const emailList = assignEmails.split(/[\n,]+/).map(e => e.trim()).filter(e => e);
    try {
      const res = await fetch(`${API_BASE}/api/role-assignments`, {
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
        body: JSON.stringify({ emails: emailList, role: assignRole, duration_hrs: assignDuration })
      });
      if (res.ok) { setAssignEmails(""); setAssignRole(""); setAssignDuration(""); fetchData(); setIsAddingMember(false); }
      else { alert((await res.json()).error); }
    } catch (err) { alert("Error assigning roles"); }
  };

  const bulkUpdateRole = async (role) => {
    if (selectedEmails.length === 0) return;
    try {
      const res = await fetch(`${API_BASE}/api/role-assignments`, {
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
        body: JSON.stringify({ emails: selectedEmails, role })
      });
      if (res.ok) { fetchData(); setSelectedEmails([]); }
    } catch (err) { alert("Bulk update failed"); }
  };

  const deleteSelectedAssignments = async () => {
    if (selectedEmails.length === 0) return alert("No users selected.");
    if (!confirm(`Remove access for ${selectedEmails.length} users?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/role-assignments/bulk-delete`, { 
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
        body: JSON.stringify({ emails: selectedEmails })
      });
      if (res.ok) fetchData();
      else alert((await res.json()).error);
    } catch (err) { alert("Error removing assignments"); }
  };

  if (loading) return <div className="card-body">Loading Admin Settings...</div>;

  const filteredAssignments = assignments
    .filter(a => {
      const email = (a.email || "").toLowerCase();
      const role = (a.role || "").toLowerCase();
      const name = email.split('@')[0];
      const query = (memberSearch || "").toLowerCase();
      return email.includes(query) || role.includes(query) || name.includes(query);
    })
    .sort((a, b) => a.email.localeCompare(b.email));

  const roleMembers = assignments.filter(a => a.role === editingRole?.name);

  const getRoleColor = (roleName) => {
    const role = roles.find(r => r.name === roleName);
    if (role && role.color) return role.color;
    return DEFAULT_ROLE_COLORS[roleName.toLowerCase()] || "#7289da";
  };

  return (
    <div className="grid">
      <style>{`
        .toggle-switch { position: relative; display: inline-block; width: 44px; height: 24px; }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #cbd5e0; transition: .4s; border-radius: 24px; }
        .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #5865F2; }
        input:checked + .slider:before { transform: translateX(20px); }

        .editor-tab { padding: 10px 20px; cursor: pointer; font-weight: 600; color: #4f6073; border-bottom: 2px solid transparent; transition: 0.2s; }
        .editor-tab.active { color: #5865F2; border-bottom-color: #5865F2; }
        .perm-item { padding: 16px 0; border-bottom: 1px solid #edf2f7; display: flex; justify-content: space-between; align-items: center; }
        .perm-item:last-child { border-bottom: none; }

        .member-table th { font-size: 0.75rem; color: #4e5058; text-transform: uppercase; font-weight: 700; padding: 12px 16px; border: none; }
        .member-row { transition: background 0.1s; border-bottom: 1px solid #f2f3f5; }
        .member-row:hover { background: #f2f3f5; }
        
        .role-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; border: 1px solid transparent; transition: all 0.2s; }
        .avatar-circle { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 0.95rem; margin-right: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .action-icon { padding: 8px; border-radius: 8px; cursor: pointer; color: #4e5058; transition: all 0.2s; display: flex; align-items: center; justify-content: center; }
        .action-icon:hover { background: #fee2e2; color: #ef4444; }

        .color-dot { width: 24px; height: 24px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; transition: 0.2s; }
        .color-dot.active { border-color: #5865f2; transform: scale(1.1); }
      `}</style>

      {/* Roles Section */}
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <h3>Roles & Permissions</h3>
          <p>Define custom roles and manage access levels to different modules.</p>
        </div>
        <div className="card-body">
          {!editingRole ? (
            <>
              <button className="primary" onClick={handleCreateNewRole} style={{ width: 'fit-content' }}>+ Create New Role</button>
              <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
                <table className="report-table">
                  <thead><tr><th>Role Name</th><th>Actions</th></tr></thead>
                  <tbody>
                    {roles.map(r => (
                      <tr key={r.name}>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: getRoleColor(r.name) }}></div>
                            <strong>{r.name.charAt(0).toUpperCase() + r.name.slice(1)}</strong>
                            {r.default_duration && <span style={{ fontSize: '0.7rem', background: '#f2f3f5', padding: '2px 6px', borderRadius: '4px', color: '#4e5058' }}>⏱ {r.default_duration}h default</span>}
                          </div>
                        </td>
                        <td>
                          <button className="ghost sm" onClick={() => handleEditRole(r)} style={{ marginRight: '10px', color: '#0f8a5f' }}>Edit</button>
                          <button className="ghost sm" onClick={() => handleDuplicateRole(r)} style={{ marginRight: '10px', color: '#4f6073' }}>Duplicate</button>
                          {['admin', 'teacher', 'demo', 'student'].includes(r.name) ? null : (<button className="ghost sm" onClick={() => deleteRole(r.name)}>Delete</button>)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div className="role-editor" style={{ background: 'white', borderRadius: '16px', border: '1px solid #e4ecf4', overflow: 'hidden' }}>
              <div style={{ display: 'flex', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', padding: '0 20px' }}>
                <div className={`editor-tab ${activeEditorTab === 'display' ? 'active' : ''}`} onClick={() => setActiveEditorTab('display')}>Display</div>
                <div className={`editor-tab ${activeEditorTab === 'permissions' ? 'active' : ''}`} onClick={() => setActiveEditorTab('permissions')}>Permissions</div>
                <div className={`editor-tab ${activeEditorTab === 'members' ? 'active' : ''}`} onClick={() => setActiveEditorTab('members')}>Manage Members ({roleMembers.length})</div>
              </div>
              <div style={{ padding: '30px' }}>
                {activeEditorTab === 'display' && (
                  <div style={{ maxWidth: '600px', display: 'flex', gap: '40px' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ fontWeight: '700', color: '#1a202c', display: 'block', marginBottom: '8px' }}>ROLE NAME</label>
                      <input value={roleName} onChange={e => setRoleName(e.target.value)} disabled={!editingRole.isNew} placeholder="e.g., Senior Teacher" style={{ padding: '12px', fontSize: '1rem', marginBottom: '20px' }} />
                      
                      <label style={{ fontWeight: '700', color: '#1a202c', display: 'block', marginBottom: '8px' }}>ROLE COLOR</label>
                      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px' }}>
                        {Object.values(DEFAULT_ROLE_COLORS).map(c => (
                          <div key={c} className={`color-dot ${roleColor === c ? 'active' : ''}`} style={{ background: c }} onClick={() => setRoleColor(c)}></div>
                        ))}
                        <input type="color" value={roleColor} onChange={e => setRoleColor(e.target.value)} style={{ width: '24px', height: '24px', padding: 0, border: 'none', background: 'none', cursor: 'pointer' }} />
                      </div>

                      <label style={{ fontWeight: '700', color: '#1a202c', display: 'block', marginBottom: '8px' }}>DEFAULT ROLE DURATION</label>
                      <select value={roleDefaultDuration} onChange={e => setRoleDefaultDuration(e.target.value)} style={{ padding: '10px' }}>
                        <option value="">Permanent</option>
                        <option value="1">1 Hour</option>
                        <option value="2">2 Hours</option>
                        <option value="24">24 Hours</option>
                        <option value="168">7 Days</option>
                      </select>
                      <p style={{ fontSize: '0.8rem', color: '#718096', marginTop: '6px' }}>Members added to this role will automatically expire after this time.</p>
                    </div>
                    <div style={{ width: '200px' }}>
                      <label style={{ fontWeight: '700', color: '#1a202c', display: 'block', marginBottom: '8px' }}>PREVIEW</label>
                      <div className="role-badge" style={{ background: getLightBg(roleColor), color: roleColor, padding: '8px 15px', fontSize: '0.9rem' }}>
                        <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: roleColor }}></span>
                        {roleName || "New Role"}
                      </div>
                    </div>
                  </div>
                )}
                {activeEditorTab === 'permissions' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                      <input type="text" placeholder="Search permissions..." value={permSearch} onChange={e => setPermSearch(e.target.value)} style={{ maxWidth: '400px', background: '#f1f5f9', border: 'none', borderRadius: '8px', padding: '10px 15px' }} />
                      <div style={{ display: 'flex', gap: '15px' }}>
                        <button className="ghost sm" onClick={handleGrantAll} style={{ color: '#5865F2' }}>Grant All</button>
                        <button className="ghost sm" onClick={handleClearAll} style={{ color: '#e53e3e' }}>Clear All</button>
                      </div>
                    </div>
                    <div style={{ height: '500px', overflowY: 'auto', paddingRight: '10px' }}>
                      {MODULES.map(mod => {
                        const title = MODULE_TITLES[mod] || mod;
                        if (permSearch && !title.toLowerCase().includes(permSearch.toLowerCase())) return null;
                        return (
                          <div key={mod} style={{ marginBottom: '32px' }}>
                            <h4 style={{ color: '#4a5568', fontSize: '0.75rem', fontWeight: '800', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '16px', borderBottom: '1px solid #edf2f7', paddingBottom: '8px' }}>{title}</h4>
                            {PERMISSIONS.map(perm => (
                              <div key={`${mod}-${perm}`} className="perm-item">
                                <div style={{ paddingRight: '20px' }}>
                                  <div style={{ fontWeight: '600', color: '#2d3748', marginBottom: '4px', textTransform: 'capitalize' }}>{perm} {title}</div>
                                  <div style={{ fontSize: '0.85rem', color: '#718096', lineHeight: '1.4' }}>{PERMISSION_DETAILS[perm]}</div>
                                </div>
                                <label className="toggle-switch"><input type="checkbox" checked={(rolePerms[mod] || []).includes(perm)} onChange={() => togglePermission(mod, perm)} /><span className="slider"></span></label>
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                {activeEditorTab === 'members' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                      <h4 style={{ margin: 0 }}>Members with this role</h4>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <input type="text" placeholder="Email or @domain" value={newMemberEmail} onChange={e => setNewMemberEmail(e.target.value)} style={{ width: '220px', background: '#f2f3f5', border: 'none', borderRadius: '4px', padding: '8px 12px' }} />
                        <select value={newMemberDuration} onChange={e => setNewMemberDuration(e.target.value)} style={{ width: '130px', borderRadius: '4px' }}>
                           <option value="">Permanent</option>
                           <option value="1">1 Hour</option>
                           <option value="2">2 Hours</option>
                           <option value="24">24 Hours</option>
                           <option value="168">7 Days</option>
                        </select>
                        <button className="primary" onClick={() => { 
                          if (newMemberEmail.startsWith("@")) {
                            const matching = assignments.filter(a => a.email.endsWith(newMemberEmail)).map(a => a.email);
                            if (matching.length > 0) {
                              fetch(`${API_BASE}/api/role-assignments`, {
                                method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
                                body: JSON.stringify({ emails: matching, role: editingRole.name, duration_hrs: newMemberDuration })
                              }).then(() => fetchData());
                            }
                          } else {
                            handleUpdateMemberRole(newMemberEmail, editingRole.name, newMemberDuration); 
                          }
                          setNewMemberEmail(""); 
                        }} style={{ borderRadius: '4px', padding: '8px 16px' }}>Add Match</button>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                      {roleMembers.length === 0 ? (<p style={{ color: '#4e5058', fontSize: '0.9rem' }}>No users are currently assigned to this role.</p>) : (
                        roleMembers.map(m => (
                          <div key={m.email} style={{ background: '#f2f3f5', padding: '8px 14px', borderRadius: '20px', fontSize: '0.9rem', fontWeight: '600', color: '#060607', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {m.email} 
                            {m.expires_at && <span style={{ color: '#ed4245', fontSize: '0.75rem' }}>⏱</span>}
                            <span style={{ cursor: 'pointer', color: '#ef4444', fontSize: '1.2rem', lineHeight: 1 }} title="Remove" onClick={() => handleUpdateMemberRole(m.email, "visitor")}>&times;</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
                <div style={{ display: 'flex', gap: '1rem', marginTop: '30px', paddingTop: '20px', borderTop: '1px solid #e2e8f0' }}>
                  <button className="primary" onClick={saveRole}>Save Changes</button>
                  <button className="ghost" onClick={() => setEditingRole(null)}>Discard</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Member Management Section */}
      <div className="card" style={{ gridColumn: '1 / -1', background: 'white' }}>
        <div style={{ padding: '24px' }}>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '700' }}>Server Members</h2>
          <p style={{ color: '#4e5058', margin: '8px 0 24px 0', fontSize: '0.95rem', lineHeight: '1.5' }}>Authorized users can access ClassOps based on their roles. Find and manage members quickly below.</p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h3 style={{ margin: 0, fontSize: '0.9rem', color: '#4e5058', textTransform: 'uppercase', letterSpacing: '0.02em' }}>All Members — {filteredAssignments.length}</h3>
            <div style={{ display: 'flex', gap: '12px' }}>
              <input type="text" placeholder="Search members..." value={memberSearch} onChange={e => setMemberSearch(e.target.value)} style={{ width: '300px', background: '#f2f3f5', border: 'none', borderRadius: '4px', padding: '8px 12px', fontSize: '0.9rem' }} />
              <button className="primary" onClick={() => setIsAddingMember(!isAddingMember)} style={{ borderRadius: '4px', padding: '8px 16px' }}>{isAddingMember ? "Close" : "+ Add Members"}</button>
              {selectedEmails.length > 0 && (
                <div style={{ display: 'flex', gap: '8px' }}>
                   <select onChange={(e) => bulkUpdateRole(e.target.value)} style={{ borderRadius: '4px', background: '#5865f2', color: 'white', border: 'none', padding: '8px' }}>
                      <option value="">Bulk Assign Role...</option>
                      {roles.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
                   </select>
                   <button onClick={deleteSelectedAssignments} style={{ borderRadius: '4px', background: '#f04747', color: 'white', border: 'none', padding: '8px 16px', fontWeight: '600' }}>Revoke Access</button>
                </div>
              )}
            </div>
          </div>

          {isAddingMember && (
            <div style={{ background: '#f8fafc', padding: '24px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
              <h4 style={{ marginTop: 0, marginBottom: '16px' }}>Quick Add Members</h4>
              <div style={{ display: 'flex', gap: '20px' }}>
                <textarea placeholder="Paste emails separated by commas..." value={assignEmails} onChange={e => setAssignEmails(e.target.value)} style={{ flex: 1, minHeight: '100px', borderRadius: '4px' }} />
                <div style={{ width: '250px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <select value={assignRole} onChange={e => setAssignRole(e.target.value)} style={{ borderRadius: '4px' }}>
                    <option value="">Select Initial Role</option>
                    {roles.map(r => <option key={r.name} value={r.name}>{r.name.charAt(0).toUpperCase() + r.name.slice(1)}</option>)}
                  </select>
                  <select value={assignDuration} onChange={e => setAssignDuration(e.target.value)} style={{ borderRadius: '4px' }}>
                    <option value="">Permanent Access</option>
                    <option value="1">Expire in 1 Hour</option>
                    <option value="12">Expire in 12 Hours</option>
                    <option value="24">Expire in 24 Hours</option>
                    <option value="168">Expire in 7 Days</option>
                  </select>
                  <button className="primary" onClick={saveAssignments} style={{ width: '100%', borderRadius: '4px' }}>Add to Server</button>
                </div>
              </div>
            </div>
          )}

          <div style={{ overflowX: 'auto' }}>
            <table className="member-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e3e5e8' }}>
                  <th style={{ width: '40px' }}><input type="checkbox" onChange={(e) => setSelectedEmails(e.target.checked ? filteredAssignments.map(a => a.email) : [])} checked={selectedEmails.length > 0 && selectedEmails.length === filteredAssignments.length} /></th>
                  <th style={{ textAlign: 'left' }}>NAME</th>
                  <th style={{ textAlign: 'left' }}>ROLES</th>
                  <th style={{ textAlign: 'left' }}>EXPIRY</th>
                  <th style={{ textAlign: 'right' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {filteredAssignments.length === 0 ? (
                  <tr><td colSpan="5" style={{ textAlign: 'center', padding: '60px', color: '#4e5058' }}>No members found matching your search</td></tr>
                ) : (
                  filteredAssignments.map(user => {
                    const { initial, color, displayName } = getAvatarInfo(user.email);
                    const rColor = getRoleColor(user.role);
                    
                    return (
                      <tr key={user.email} className="member-row">
                        <td style={{ padding: '12px 16px' }}><input type="checkbox" checked={selectedEmails.includes(user.email)} onChange={() => setSelectedEmails(prev => prev.includes(user.email) ? prev.filter(e => e !== user.email) : [...prev, user.email])} /></td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center' }}>
                            <div className="avatar-circle" style={{ background: color }}>{initial}</div>
                            <div>
                              <div style={{ fontWeight: '700', color: '#060607', fontSize: '0.95rem' }}>{displayName}</div>
                              <div style={{ fontSize: '0.8rem', color: '#4e5058' }}>{user.email}</div>
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', position: 'relative' }}>
                            <div className="role-badge" style={{ background: getLightBg(rColor), color: rColor }}>
                              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: rColor }}></span>
                              {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                            </div>
                            <select value={user.role} title="Change Role" onChange={(e) => handleUpdateMemberRole(user.email, e.target.value)} style={{ width: '100%', height: '100%', opacity: 0, position: 'absolute', cursor: 'pointer' }}>
                              {roles.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
                            </select>
                          </div>
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          {user.expires_at ? (
                            <span style={{ fontSize: '0.8rem', color: '#ed4245', fontWeight: '600' }}>
                               ⌛ {new Date(user.expires_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.8rem', color: '#b9bbbe' }}>∞ Permanent</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                          <div className="action-icon" title="Revoke Access" onClick={() => { if (confirm(`Revoke access for ${user.email}?`)) { setSelectedEmails([user.email]); deleteSelectedAssignments(); } }}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="18" y1="8" x2="23" y2="13"></line><line x1="23" y1="8" x2="18" y2="13"></line></svg></div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
