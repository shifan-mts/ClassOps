import React from 'react';
import { Plus, FileText, Calendar, Users, ChevronRight, MoreVertical } from 'lucide-react';

const AssignmentCard = ({ assignment }) => (
    <div className="bg-white rounded-3xl border border-light-secondary/50 shadow-sm p-6 hover:shadow-md transition-all group">
        <div className="flex justify-between items-start mb-6">
            <div className="p-3 bg-light-bg rounded-2xl text-dark-primary group-hover:bg-dark-highlight transition-colors">
                <FileText size={20} />
            </div>
            <button className="p-2 text-light-text hover:bg-light-bg rounded-lg opacity-0 group-hover:opacity-100 transition-all">
                <MoreVertical size={18} />
            </button>
        </div>

        <h3 className="text-lg font-bold text-dark-primary leading-tight">{assignment.title}</h3>
        <p className="text-xs font-bold text-dark-accent mt-1 flex items-center gap-1">
            {assignment.course}
        </p>

        <div className="mt-6 flex items-center gap-4 text-xs font-bold text-light-text">
            <div className="flex items-center gap-1.5 bg-light-bg px-2.5 py-1.5 rounded-lg">
                <Calendar size={14} />
                {assignment.due_date}
            </div>
            <div className="flex items-center gap-1.5 bg-light-bg px-2.5 py-1.5 rounded-lg">
                <Users size={14} />
                {assignment.submissions}/{assignment.total}
            </div>
        </div>

        <div className="mt-6 flex items-center justify-between gap-4">
            <div className="flex-1 overflow-hidden">
                <div className="flex justify-between text-[10px] font-bold text-light-text uppercase tracking-wider mb-1 px-1">
                    <span>Graded</span>
                    <span>{Math.round((assignment.graded / assignment.submissions) * 100)}%</span>
                </div>
                <div className="w-full bg-light-bg h-1.5 rounded-full overflow-hidden">
                    <div
                        className="bg-dark-primary h-full"
                        style={{ width: `${(assignment.graded / assignment.submissions) * 100}%` }}
                    ></div>
                </div>
            </div>
            <button className="p-2 bg-dark-highlight text-dark-primary rounded-xl hover:bg-dark-accent hover:text-white transition-all">
                <ChevronRight size={18} />
            </button>
        </div>
    </div>
);

const Assignments = () => {
    const dummyAssignments = [
        { id: 1, title: 'Pointer Manipulation & Memory Mgmt', course: 'Data Structures', due_date: 'Oct 15, 2025', submissions: 42, total: 45, graded: 38 },
        { id: 2, title: 'BFS vs DFS Implementation', course: 'Algorithms', due_date: 'Oct 18, 2025', submissions: 15, total: 42, graded: 0 },
        { id: 3, title: 'SQL Joins & Normalization', course: 'Database Systems', due_date: 'Oct 12, 2025', submissions: 50, total: 50, graded: 50 },
        { id: 4, title: 'CPU Scheduling Algorithms', course: 'Operating Systems', due_date: 'Oct 20, 2025', submissions: 10, total: 38, graded: 0 },
    ];

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Assignments</h1>
                    <p className="text-light-text mt-1">Create, track, and grade student submissions.</p>
                </div>
                <button className="bg-dark-primary text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-dark-secondary transition-all shadow-lg shadow-dark-primary/20">
                    <Plus size={20} />
                    New Assignment
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                <div className="bg-white rounded-3xl border-2 border-dashed border-light-secondary/50 flex flex-col items-center justify-center p-8 text-center group cursor-pointer hover:border-dark-accent transition-all">
                    <div className="w-16 h-16 rounded-full bg-light-bg flex items-center justify-center text-light-text group-hover:bg-dark-highlight group-hover:text-dark-primary transition-all mb-4">
                        <Plus size={32} />
                    </div>
                    <h3 className="text-sm font-bold text-dark-primary">Create New</h3>
                    <p className="text-xs text-light-text mt-1">Start a new evaluation task</p>
                </div>
                {dummyAssignments.map(asgn => (
                    <AssignmentCard key={asgn.id} assignment={asgn} />
                ))}
            </div>
        </div>
    );
};

export default Assignments;
