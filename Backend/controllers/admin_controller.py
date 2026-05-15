from flask import jsonify, request, session, render_template_string
from repositories import dynamodb_repository as db
import os

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "username")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

def admin_login():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        session.modified = True
        return jsonify({"success": True, "message": "Logged in as admin"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

def admin_logout():
    session.pop("admin_logged_in", None)
    return jsonify({"success": True, "message": "Logged out"})

def check_admin_auth():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    return None

def get_components():
    comps = db.scan_all_components()
    return jsonify(comps)

# The UI for the admin dashboard
ADMIN_UI_HTML = """
{% raw %}
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ClassOps Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        border: "hsl(240 3.7% 15.9%)",
                        input: "hsl(240 3.7% 15.9%)",
                        ring: "hsl(240 4.9% 83.9%)",
                        background: "hsl(240 10% 3.9%)",
                        foreground: "hsl(0 0% 98%)",
                        primary: {
                            DEFAULT: "hsl(0 0% 98%)",
                            foreground: "hsl(240 5.9% 10%)",
                        },
                        secondary: {
                            DEFAULT: "hsl(240 3.7% 15.9%)",
                            foreground: "hsl(0 0% 98%)",
                        },
                        destructive: {
                            DEFAULT: "hsl(0 62.8% 30.6%)",
                            foreground: "hsl(0 0% 98%)",
                        },
                        muted: {
                            DEFAULT: "hsl(240 3.7% 15.9%)",
                            foreground: "hsl(240 5% 64.9%)",
                        },
                        accent: {
                            DEFAULT: "hsl(240 3.7% 15.9%)",
                            foreground: "hsl(0 0% 98%)",
                        },
                        popover: {
                            DEFAULT: "hsl(240 10% 3.9%)",
                            foreground: "hsl(0 0% 98%)",
                        },
                        card: {
                            DEFAULT: "hsl(240 10% 3.9%)",
                            foreground: "hsl(0 0% 98%)",
                        },
                    },
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; font-size: 14px; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: hsl(240 10% 3.9%); }
        ::-webkit-scrollbar-thumb { background: hsl(240 3.7% 15.9%); border-radius: 3px; }
        .tab-active { color: white !important; border-bottom: 2px solid white; font-weight: 600; }
        input, select { background-color: transparent !important; }
    </style>
</head>
<body class="bg-background text-foreground min-h-screen">
    <div id="app">
        <!-- Login Screen -->
        <div v-if="!isLoggedIn" class="flex items-center justify-center min-h-screen px-4">
            <div class="w-full max-w-sm border border-border bg-card p-8 rounded-lg shadow-2xl relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                <div class="flex flex-col space-y-1 text-center mb-8">
                    <h1 class="text-2xl font-semibold tracking-tight text-white uppercase tracking-widest">Administrative Auth</h1>
                </div>
                <div class="space-y-5">
                    <div class="space-y-1">
                        <label class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Identifier</label>
                        <input v-model="loginData.username" type="text" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-1 focus:ring-white/20 outline-none">
                    </div>
                    <div class="space-y-1">
                        <label class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Passphrase</label>
                        <input v-model="loginData.password" @keyup.enter="login" type="password" class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:ring-1 focus:ring-white/20 outline-none">
                    </div>
                    <button @click="login" class="inline-flex items-center justify-center rounded-md text-xs font-bold uppercase tracking-widest bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 w-full transition-all active:scale-[0.98]">
                        Authorize
                    </button>
                </div>
            </div>
        </div>

        <!-- Dashboard -->
        <div v-else class="flex flex-col min-h-screen">
            <header class="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur shadow-sm">
                <div class="container flex h-14 items-center justify-between px-6 mx-auto max-w-6xl">
                    <div class="flex items-center gap-3">
                        <div class="w-7 h-7 bg-primary rounded flex items-center justify-center text-primary-foreground font-bold text-sm">C</div>
                        <span class="font-bold text-sm text-white tracking-widest uppercase">ClassOps</span>
                    </div>
                    <nav class="flex items-center gap-8 text-[10px] font-bold uppercase tracking-[0.2em]">
                        <a @click="currentTab = 'roles'" :class="{'tab-active': currentTab === 'roles'}" class="cursor-pointer text-muted-foreground hover:text-white transition-all py-5">Identities</a>
                        <a @click="currentTab = 'matrix'" :class="{'tab-active': currentTab === 'matrix'}" class="cursor-pointer text-muted-foreground hover:text-white transition-all py-5">Permission Matrix</a>
                        <a @click="currentTab = 'users'" :class="{'tab-active': currentTab === 'users'}" class="cursor-pointer text-muted-foreground hover:text-white transition-all py-5">Members</a>
                        <a @click="currentTab = 'import'" :class="{'tab-active': currentTab === 'import'}" class="cursor-pointer text-muted-foreground hover:text-white transition-all py-5">Bulk</a>
                    </nav>
                    <button @click="logout" class="text-[9px] font-bold uppercase tracking-widest text-destructive hover:underline">Revoke</button>
                </div>
            </header>

            <main class="flex-1 container py-10 px-6 mx-auto max-w-6xl animate-in fade-in duration-300">
                <!-- Roles Tab -->
                <div v-if="currentTab === 'roles'" class="space-y-6">
                    <div class="flex items-center justify-between">
                        <h2 class="text-2xl font-bold tracking-tighter text-white">Institutional Roles</h2>
                        <button @click="openRoleModal()" class="h-9 px-5 rounded bg-primary text-primary-foreground text-[10px] font-bold uppercase tracking-widest hover:bg-primary/90 transition-all">
                            + Define Role
                        </button>
                    </div>

                    <div class="rounded-lg border border-border bg-card overflow-hidden">
                        <table class="w-full text-sm">
                            <thead>
                                <tr class="border-b border-border bg-muted/30 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                    <th class="p-4 text-left">Identity</th>
                                    <th class="p-4 text-left">Department</th>
                                    <th class="p-4 text-left">Badge</th>
                                    <th class="p-4 text-left">Assigned</th>
                                    <th class="p-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="role in paginatedRoles" :key="role.name" class="border-b border-border hover:bg-muted/10 transition-colors">
                                    <td class="p-4 font-bold text-white uppercase tracking-widest">{{ role.name }}</td>
                                    <td class="p-4 text-muted-foreground font-medium uppercase tracking-widest text-[9px]">{{ role.department || 'Common' }}</td>
                                    <td class="p-4">
                                        <div class="flex items-center gap-2">
                                            <div :style="{backgroundColor: role.color}" class="w-2.5 h-2.5 rounded-full"></div>
                                            <span class="font-mono text-[9px] text-muted-foreground uppercase">{{ role.color }}</span>
                                        </div>
                                    </td>
                                    <td class="p-4 font-bold text-white">{{ getRoleMemberCount(role.name) }}</td>
                                    <td class="p-4 text-right space-x-3">
                                        <button @click="openRoleModal(role)" class="text-[9px] font-bold text-muted-foreground hover:text-white uppercase tracking-widest">Edit</button>
                                        <button @click="selectRoleForMatrix(role)" class="text-[9px] font-bold text-primary hover:underline uppercase tracking-widest">Matrix</button>
                                        <button v-if="!['teacher', 'student'].includes(role.name)" @click="deleteRole(role.name)" class="text-[9px] font-bold text-destructive hover:underline uppercase tracking-widest">Purge</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <!-- Pagination for Roles -->
                    <div class="flex items-center justify-between mt-4 px-2">
                        <p class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Page {{ rolesPage }} of {{ totalRolePages }}</p>
                        <div class="flex gap-2">
                            <button @click="rolesPage--" :disabled="rolesPage === 1" class="h-8 px-3 rounded border border-border text-[9px] font-bold uppercase disabled:opacity-20 hover:bg-white/5 transition-all">Prev</button>
                            <button @click="rolesPage++" :disabled="rolesPage === totalRolePages" class="h-8 px-3 rounded border border-border text-[9px] font-bold uppercase disabled:opacity-20 hover:bg-white/5 transition-all">Next</button>
                        </div>
                    </div>
                </div>

                <!-- Matrix Tab -->
                <div v-if="currentTab === 'matrix'" class="space-y-6">
                    <div class="flex items-center justify-between">
                        <h2 class="text-2xl font-bold tracking-tighter text-white">Permission Matrix</h2>
                        <div class="flex items-center gap-4">
                             <select v-model="selectedMatrixRoleName" class="h-9 bg-card border border-border rounded px-3 text-[10px] font-bold uppercase tracking-widest text-white outline-none">
                                <option value="">Select Identity...</option>
                                <option v-for="r in roles" :key="r.name" :value="r.name">{{ r.name.toUpperCase() }} ({{ r.department || 'Common' }})</option>
                            </select>
                            <button @click="saveAllRoles" class="h-9 px-6 rounded bg-primary text-primary-foreground text-[10px] font-bold uppercase tracking-widest hover:bg-primary/90 shadow-lg active:scale-95 transition-all">
                                Publish Matrix
                            </button>
                        </div>
                    </div>

                    <div v-if="selectedMatrixRole" class="rounded-lg border border-border bg-card shadow-lg overflow-hidden">
                        <table class="w-full text-sm border-collapse">
                            <thead>
                                <tr class="bg-muted/30 border-b border-border text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                    <th class="p-5 text-left border-r border-border w-1/2">Institutional Feature</th>
                                    <th class="p-5 text-center border-r border-border">VIEW</th>
                                    <th class="p-5 text-center">EDIT</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="comp in components" :key="comp.id" class="border-b border-border hover:bg-muted/5 transition-colors">
                                    <td class="p-5 border-r border-border">
                                        <div class="font-bold text-sm text-white leading-tight mb-1">{{ comp.name }}</div>
                                        <p class="text-[10px] text-muted-foreground leading-relaxed font-medium">{{ comp.description }}</p>
                                    </td>
                                    <td v-for="perm in ['view', 'edit']" :key="perm" class="p-5 text-center border-r border-border last:border-r-0">
                                        <div class="flex items-center justify-center">
                                            <input type="checkbox" 
                                                   :checked="selectedMatrixRole.permissions[comp.id] && selectedMatrixRole.permissions[comp.id].includes(perm)"
                                                   @change="togglePermission(selectedMatrixRole, comp.id, perm)"
                                                   class="w-6 h-6 rounded border-border bg-background text-primary focus:ring-0 cursor-pointer accent-white">
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div v-else class="flex flex-col items-center justify-center py-24 border-2 border-dashed border-border rounded-xl bg-muted/5">
                        <p class="text-muted-foreground text-[10px] font-bold uppercase tracking-widest">Select an identity tier to configure access levels</p>
                    </div>
                </div>

                <!-- Bulk Actions Tab -->
                <div v-if="currentTab === 'import'" class="space-y-6">
                    <h2 class="text-2xl font-bold tracking-tighter text-white text-center">Institutional Bulk Deployment</h2>
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
                        <div class="border border-border bg-card p-10 rounded-2xl space-y-6 shadow-xl">
                            <h3 class="text-sm font-bold text-white uppercase tracking-widest">Drag-and-Drop Deployment</h3>
                            <div @dragover.prevent @drop.prevent="handleFileDrop" 
                                 class="flex flex-col items-center justify-center p-12 border-2 border-dashed border-border rounded-xl hover:border-primary/50 transition-all bg-muted/5 cursor-pointer"
                                 @click="$refs.fileInput.click()">
                                <input type="file" ref="fileInput" @change="handleFileSelect" class="hidden" accept=".json">
                                <p class="text-[11px] font-bold uppercase tracking-widest text-white">{{ selectedFile ? selectedFile.name : 'Choose Institutional Specification JSON' }}</p>
                            </div>
                            <button @click="uploadFile" :disabled="!selectedFile" class="h-11 px-8 rounded-lg bg-white text-black text-[10px] font-bold uppercase tracking-widest hover:bg-white/90 w-full disabled:opacity-20 transition-all shadow-xl shadow-white/5">
                                Start Onboarding
                            </button>
                        </div>
                        <div class="border border-border bg-card p-10 rounded-2xl overflow-hidden bg-black/20">
                             <h3 class="text-sm font-bold text-white uppercase tracking-widest mb-6">Required Specification Schema</h3>
                             <pre class="text-[10px] text-primary font-mono leading-relaxed p-4 rounded-lg bg-black/40 border border-white/5 uppercase tracking-widest">
{
  "roles": [{
    "name": "dean_of_science",
    "department": "Physics",
    "color": "#ff0000"
  }],
  "assignments": [{
    "email": "dean@college.edu",
    "role": "dean_of_science"
  }]
}</pre>
                        </div>
                    </div>
                </div>

                <!-- Member Registry Tab -->
                <div v-if="currentTab === 'users'" class="space-y-6">
                    <div class="flex items-center justify-between">
                        <h2 class="text-2xl font-bold tracking-tighter text-white">Member Registry</h2>
                        <button @click="openUserModal()" class="h-9 px-5 rounded bg-primary text-primary-foreground text-[10px] font-bold uppercase tracking-widest hover:bg-primary/90 transition-all">
                            + Provision Member
                        </button>
                    </div>

                    <div class="rounded-lg border border-border bg-card overflow-hidden shadow-xl">
                         <table class="w-full text-sm">
                            <thead>
                                <tr class="border-b border-border bg-muted/50 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                    <th class="p-4 text-left">Identifier</th>
                                    <th class="p-4 text-left">Identity Tier</th>
                                    <th class="p-4 text-left">Lifespan</th>
                                    <th class="p-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="user in paginatedUsers" :key="user.email" class="border-b border-border hover:bg-muted/20 transition-colors">
                                    <td class="p-4 font-bold text-white text-base tracking-tight">{{ user.email }}</td>
                                    <td class="p-4 font-medium">
                                        <div class="flex flex-col">
                                            <span class="text-[11px] font-bold uppercase tracking-widest text-primary">{{ user.role }}</span>
                                            <span class="text-[8px] uppercase font-bold text-muted-foreground tracking-widest mt-1.5">{{ getRoleDept(user.role) }}</span>
                                        </div>
                                    </td>
                                    <td class="p-4">
                                        <span v-if="!user.expires_at" class="text-[10px] font-bold text-green-500 uppercase tracking-widest">Permanent</span>
                                        <span v-else class="text-[10px] font-bold text-yellow-500 uppercase tracking-widest italic">{{ formatDate(user.expires_at) }}</span>
                                    </td>
                                    <td class="p-4 text-right">
                                        <button @click="deleteAssignment(user.email)" class="text-[9px] font-bold uppercase tracking-widest text-destructive hover:underline">Revoke Authority</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <!-- Pagination for Users -->
                    <div class="flex items-center justify-between mt-4 px-2">
                        <p class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Page {{ usersPage }} of {{ totalUserPages }}</p>
                        <div class="flex gap-2">
                            <button @click="usersPage--" :disabled="usersPage === 1" class="h-8 px-3 rounded border border-border text-[9px] font-bold uppercase disabled:opacity-20 hover:bg-white/5 transition-all">Prev</button>
                            <button @click="usersPage++" :disabled="usersPage === totalUserPages" class="h-8 px-3 rounded border border-border text-[9px] font-bold uppercase disabled:opacity-20 hover:bg-white/5 transition-all">Next</button>
                        </div>
                    </div>
                </div>
            </main>
        </div>

        <!-- Role Modal -->
        <div v-if="showRoleModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/95 backdrop-blur-md animate-in fade-in duration-200">
            <div class="w-full max-w-sm border border-border bg-card p-10 rounded-2xl shadow-2xl space-y-8 relative overflow-hidden">
                <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                <div class="space-y-1">
                    <h3 class="text-2xl font-bold text-white tracking-tight uppercase tracking-tighter">{{ editingRole.isNew ? 'Define Identity' : 'Shift Identity' }}</h3>
                </div>
                <div class="space-y-6">
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Internal System ID</label>
                        <input v-model="editingRole.name" type="text" :disabled="!editingRole.isNew" class="h-11 w-full rounded border border-input bg-background/50 px-4 text-sm font-semibold text-white focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Parent Department</label>
                        <input v-model="editingRole.department" type="text" class="h-11 w-full rounded border border-input bg-background/50 px-4 text-sm font-semibold text-white focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Badge Color</label>
                        <div class="flex items-center gap-4">
                            <input v-model="editingRole.color" type="color" class="h-11 w-16 border-none bg-transparent cursor-pointer rounded overflow-hidden shadow-lg">
                            <input v-model="editingRole.color" type="text" class="flex-1 h-11 rounded border border-input bg-background/50 px-4 text-xs font-bold text-white uppercase tracking-widest">
                        </div>
                    </div>
                </div>
                <div class="flex items-center justify-end space-x-6 pt-6 border-t border-border text-[10px] font-bold uppercase tracking-widest">
                    <button @click="showRoleModal = false" class="hover:underline text-muted-foreground">Cancel</button>
                    <button @click="saveRole" class="h-10 px-8 rounded bg-white text-black active:scale-95 transition-all">
                        Commit
                    </button>
                </div>
            </div>
        </div>

        <!-- User Modal -->
        <div v-if="showUserModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/95 backdrop-blur-md animate-in fade-in duration-200">
            <div class="w-full max-w-sm border border-border bg-card p-10 rounded-2xl shadow-2xl space-y-8 relative overflow-hidden">
                 <div class="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                <div class="space-y-1">
                    <h3 class="text-2xl font-bold text-white tracking-tight uppercase tracking-tighter">Member Provision</h3>
                </div>
                <div class="space-y-6">
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Google Identifier</label>
                        <input v-model="userData.email" type="email" class="h-11 w-full rounded border border-input bg-background/50 px-4 text-sm font-semibold text-white focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Identity Tier</label>
                        <select v-model="userData.role" class="h-11 w-full rounded border border-input bg-background/50 px-4 text-[10px] font-bold uppercase tracking-widest text-white focus:ring-1 focus:ring-primary outline-none appearance-none cursor-pointer">
                            <option v-for="role in roles" :key="role.name" :value="role.name">{{ role.name.toUpperCase() }} ({{ role.department || 'Common' }})</option>
                        </select>
                    </div>
                    <div class="space-y-2">
                        <label class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Authority Lifespan (Hrs)</label>
                        <input v-model="userData.duration" type="number" placeholder="PERMANENT" class="h-11 w-full rounded border border-input bg-background/50 px-4 text-sm font-bold text-white focus:ring-1 focus:ring-primary outline-none transition-all">
                    </div>
                </div>
                <div class="flex items-center justify-end space-x-6 pt-6 border-t border-border text-[10px] font-bold uppercase tracking-widest">
                    <button @click="showUserModal = false" class="hover:underline text-muted-foreground">Cancel</button>
                    <button @click="saveAssignment" class="h-10 px-8 rounded bg-white text-black active:scale-95 transition-all">
                        Authorize
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script>
        const { createApp } = Vue

        createApp({
            data() {
                return {
                    isLoggedIn: false,
                    currentTab: 'roles',
                    loginData: { username: '', password: '' },
                    roles: [],
                    components: [],
                    assignments: [],
                    showRoleModal: false,
                    editingRole: { name: '', color: '#7289da', department: 'Common', permissions: {}, isNew: true },
                    showUserModal: false,
                    userData: { email: '', role: '', duration: '' },
                    selectedFile: null,
                    selectedMatrixRoleName: '',
                    pageSize: 10,
                    rolesPage: 1,
                    usersPage: 1
                }
            },
            computed: {
                selectedMatrixRole() {
                    return this.roles.find(r => r.name === this.selectedMatrixRoleName)
                },
                totalRolePages() {
                    return Math.ceil(this.roles.length / this.pageSize) || 1
                },
                paginatedRoles() {
                    const start = (this.rolesPage - 1) * this.pageSize
                    return this.roles.slice(start, start + this.pageSize)
                },
                totalUserPages() {
                    return Math.ceil(this.assignments.length / this.pageSize) || 1
                },
                paginatedUsers() {
                    const start = (this.usersPage - 1) * this.pageSize
                    return this.assignments.slice(start, start + this.pageSize)
                }
            },
            mounted() {
                this.checkSession()
            },
            methods: {
                async checkSession() {
                    try {
                        const res = await fetch('/api/admin/roles')
                        if (res.ok) {
                            this.isLoggedIn = true
                            this.fetchData()
                        }
                    } catch (e) {}
                },
                async login() {
                    const res = await fetch('/api/admin/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.loginData)
                    })
                    if (res.ok) {
                        this.isLoggedIn = true
                        this.fetchData()
                    } else {
                        alert('Unauthorized')
                    }
                },
                async logout() {
                    await fetch('/api/admin/logout', { method: 'POST' })
                    this.isLoggedIn = false
                },
                async fetchData() {
                    const [resRoles, resComps, resAssig] = await Promise.all([
                        fetch('/api/admin/roles'),
                        fetch('/api/admin/components'),
                        fetch('/api/admin/assignments')
                    ])
                    this.roles = await resRoles.json()
                    this.components = await resComps.json()
                    this.assignments = await resAssig.json()
                },
                getRoleColor(roleName) {
                    const role = this.roles.find(r => r.name === roleName)
                    return role ? role.color : '#ffffff'
                },
                getRoleDept(roleName) {
                    const role = this.roles.find(r => r.name === roleName)
                    return role ? (role.department || 'Common') : 'Common'
                },
                getRoleMemberCount(roleName) {
                    return this.assignments.filter(a => a.role === roleName).length
                },
                formatDate(iso) {
                    return new Date(iso).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})
                },
                openRoleModal(role = null) {
                    if (role) {
                        this.editingRole = JSON.parse(JSON.stringify(role))
                        this.editingRole.isNew = false
                    } else {
                        this.editingRole = { name: '', color: '#7289da', department: 'Common', permissions: {}, isNew: true }
                    }
                    this.showRoleModal = true
                },
                async saveRole() {
                    const method = this.editingRole.isNew ? 'POST' : 'PUT'
                    const url = this.editingRole.isNew ? '/api/admin/roles' : `/api/admin/roles/${this.editingRole.name}`
                    const res = await fetch(url, {
                        method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.editingRole)
                    })
                    if (res.ok) {
                        this.showRoleModal = false
                        this.fetchData()
                    }
                },
                async deleteRole(name) {
                    if (confirm(`Delete Role '${name}'?`)) {
                        const res = await fetch(`/api/admin/roles/${name}`, { method: 'DELETE' })
                        if (res.ok) this.fetchData()
                        else {
                            const data = await res.json()
                            alert(data.error)
                        }
                    }
                },
                selectRoleForMatrix(role) {
                    this.selectedMatrixRoleName = role.name;
                    this.currentTab = 'matrix';
                },
                togglePermission(role, compId, perm) {
                    if (!role.permissions[compId]) role.permissions[compId] = []
                    const index = role.permissions[compId].indexOf(perm)
                    if (index > -1) {
                        role.permissions[compId].splice(index, 1)
                    } else {
                        role.permissions[compId].push(perm)
                    }
                },
                async saveAllRoles() {
                    for (const role of this.roles) {
                        await fetch(`/api/admin/roles/${role.name}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(role)
                        })
                    }
                    alert('Sync Success')
                    this.fetchData()
                },
                openUserModal() {
                    this.userData = { email: '', role: this.roles[0]?.name || '', duration: '' }
                    this.showUserModal = true
                },
                async saveAssignment() {
                    if(!this.userData.email) return alert('Email Required');
                    const res = await fetch('/api/admin/assignments', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            email: this.userData.email,
                            role: this.userData.role,
                            duration_hrs: this.userData.duration
                        })
                    })
                    if (res.ok) {
                        this.showUserModal = false
                        this.fetchData()
                    }
                },
                async deleteAssignment(email) {
                    if (confirm(`Revoke access for ${email}?`)) {
                        const res = await fetch(`/api/admin/assignments/${email}`, { method: 'DELETE' })
                        if (res.ok) this.fetchData()
                    }
                },
                handleFileSelect(e) {
                    this.selectedFile = e.target.files[0]
                },
                handleFileDrop(e) {
                    this.selectedFile = e.dataTransfer.files[0]
                },
                async uploadFile() {
                    if (!this.selectedFile) return
                    const reader = new FileReader()
                    reader.onload = async (e) => {
                        try {
                            const data = JSON.parse(e.target.result)
                            const res = await fetch('/api/admin/bulk-import', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(data)
                            })
                            const result = await res.json()
                            alert(result.message || result.error)
                            this.selectedFile = null
                            this.fetchData()
                        } catch (err) {
                            alert('Invalid JSON')
                        }
                    }
                    reader.readAsText(this.selectedFile)
                }
            }
        }).mount('#app')
    </script>
</body>
</html>
{% endraw %}
"""

def serve_admin_ui():
    return render_template_string(ADMIN_UI_HTML)
