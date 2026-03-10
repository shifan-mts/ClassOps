import React from 'react';
import { NavLink } from 'react-router-dom';
import {
    LayoutDashboard,
    BookOpen,
    Users,
    CheckSquare,
    FileText,
    BarChart3,
    FileQuestion,
    FileBarChart,
    LogOut
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const Sidebar = () => {
    const navItems = [
        { name: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
        { name: 'Courses', icon: BookOpen, path: '/courses' },
        { name: 'Students', icon: Users, path: '/students' },
        { name: 'Attendance', icon: CheckSquare, path: '/attendance' },
        { name: 'Assignments', icon: FileText, path: '/assignments' },
        { name: 'Analytics', icon: BarChart3, path: '/analytics' },
        { name: 'Q-Generator', icon: FileQuestion, path: '/question-generator' },
        { name: 'Reports', icon: FileBarChart, path: '/reports' },
    ];

    return (
        <aside className="w-64 bg-dark-primary text-white h-screen flex flex-col fixed left-0 top-0 transition-all duration-300">
            <div className="p-6">
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                    <span className="bg-dark-highlight p-1 rounded-md text-dark-primary">TF</span>
                    TeacherFlow
                </h1>
            </div>

            <nav className="flex-1 px-4 space-y-1 overflow-y-auto mt-4">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => cn(
                            "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200",
                            isActive
                                ? "bg-dark-highlight text-dark-primary shadow-lg shadow-dark-primary/20"
                                : "text-white/70 hover:text-white hover:bg-white/10"
                        )}
                    >
                        <item.icon size={20} />
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 mt-auto border-t border-white/10">
                <button className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-white/70 hover:text-white hover:bg-white/10 w-full transition-all">
                    <LogOut size={20} />
                    Logout
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
