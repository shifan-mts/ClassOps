import React from 'react';
import { Search, Bell, User } from 'lucide-react';

const Navbar = () => {
    return (
        <header className="h-16 bg-white border-b border-light-secondary flex items-center justify-between px-8 sticky top-0 z-10">
            <div className="flex items-center gap-4 bg-light-bg px-4 py-2 rounded-xl w-96">
                <Search size={18} className="text-light-text/50" />
                <input
                    type="text"
                    placeholder="Search students, courses..."
                    className="bg-transparent border-none outline-none text-sm w-full placeholder:text-light-text/40"
                />
            </div>

            <div className="flex items-center gap-6">
                <button className="relative p-2 text-light-text hover:bg-light-bg rounded-lg transition-colors">
                    <Bell size={20} />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
                </button>

                <div className="flex items-center gap-3 pl-4 border-l border-light-secondary">
                    <div className="text-right hidden sm:block">
                        <p className="text-sm font-semibold text-dark-primary">Dr. Sarah Wilson</p>
                        <p className="text-xs text-light-text/70">Computer Science</p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-dark-accent flex items-center justify-center text-white border-2 border-white shadow-sm font-bold">
                        SW
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Navbar;
