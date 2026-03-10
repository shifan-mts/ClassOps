import React, { useState } from 'react';
import { Calendar as CalendarIcon, Check, X, Search, ChevronLeft, ChevronRight, Save } from 'lucide-react';

const Attendance = () => {
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [attendance, setAttendance] = useState({
        1: 'present',
        2: 'absent',
        3: 'present',
        4: 'late',
        5: 'present'
    });

    const students = [
        { id: 1, name: 'Alex Thompson', roll: '2022CS01' },
        { id: 2, name: 'Emma Wilson', roll: '2022CS05' },
        { id: 3, name: 'Jessica Chen', roll: '2022CS12' },
        { id: 4, name: 'Ryan Miller', roll: '2022CS08' },
        { id: 5, name: 'Sarah Parker', roll: '2022CS15' },
    ];

    const toggleStatus = (id, status) => {
        setAttendance(prev => ({ ...prev, [id]: status }));
    };

    return (
        <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Mark Attendance</h1>
                    <p className="text-light-text mt-1">Select a course and date to record student presence.</p>
                </div>
                <button className="bg-dark-primary text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-dark-secondary transition-all shadow-lg shadow-dark-primary/20">
                    <Save size={20} />
                    Save Attendance
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white p-6 rounded-3xl border border-light-secondary/50 shadow-sm">
                        <h3 className="text-sm font-bold text-dark-primary uppercase tracking-wider mb-4">Course Selection</h3>
                        <div className="space-y-2">
                            {['Data Structures', 'Algorithms', 'Operating Systems'].map((course, i) => (
                                <button
                                    key={course}
                                    className={`w-full text-left px-4 py-3 rounded-xl text-sm font-semibold transition-all ${i === 0 ? 'bg-dark-highlight text-dark-primary' : 'hover:bg-light-bg text-light-text'
                                        }`}
                                >
                                    {course}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-3xl border border-light-secondary/50 shadow-sm text-center">
                        <h3 className="text-sm font-bold text-dark-primary uppercase tracking-wider mb-4">Select Date</h3>
                        <div className="flex items-center justify-between mb-4">
                            <button className="p-2 hover:bg-light-bg rounded-lg text-light-text"><ChevronLeft size={18} /></button>
                            <span className="font-bold text-dark-primary">{new Date(date).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</span>
                            <button className="p-2 hover:bg-light-bg rounded-lg text-light-text"><ChevronRight size={18} /></button>
                        </div>
                        <input
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            className="w-full bg-light-bg px-4 py-3 rounded-xl border-none outline-none text-sm font-bold text-dark-primary"
                        />
                    </div>
                </div>

                <div className="lg:col-span-3 bg-white rounded-3xl border border-light-secondary/50 shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-light-secondary/50 flex justify-between items-center bg-light-bg/10">
                        <div className="flex items-center gap-4 bg-white px-4 py-2 rounded-xl flex-1 max-w-sm border border-light-secondary/50">
                            <Search size={18} className="text-light-text/50" />
                            <input
                                type="text"
                                placeholder="Find student..."
                                className="bg-transparent border-none outline-none text-sm w-full py-1"
                            />
                        </div>
                        <div className="flex gap-4">
                            <div className="flex items-center gap-2 text-xs font-bold text-light-text">
                                <div className="w-3 h-3 rounded-full bg-green-500"></div> Present: 42
                            </div>
                            <div className="flex items-center gap-2 text-xs font-bold text-light-text">
                                <div className="w-3 h-3 rounded-full bg-red-500"></div> Absent: 3
                            </div>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-light-bg/30 text-[10px] uppercase tracking-widest font-bold text-light-text">
                                <tr>
                                    <th className="py-4 px-8">Student Name</th>
                                    <th className="py-4 px-8">Roll Number</th>
                                    <th className="py-4 px-8 text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-light-secondary/30">
                                {students.map(student => (
                                    <tr key={student.id} className="hover:bg-light-bg/20 transition-colors">
                                        <td className="py-4 px-8 font-bold text-dark-primary text-sm">{student.name}</td>
                                        <td className="py-4 px-8 text-sm text-light-text font-medium">{student.roll}</td>
                                        <td className="py-4 px-8">
                                            <div className="flex justify-center gap-2">
                                                <button
                                                    onClick={() => toggleStatus(student.id, 'present')}
                                                    className={`p-2 rounded-xl transition-all ${attendance[student.id] === 'present'
                                                            ? 'bg-green-500 text-white shadow-lg shadow-green-200'
                                                            : 'bg-light-bg text-light-text hover:bg-green-100/50'
                                                        }`}
                                                >
                                                    <Check size={18} />
                                                </button>
                                                <button
                                                    onClick={() => toggleStatus(student.id, 'absent')}
                                                    className={`p-2 rounded-xl transition-all ${attendance[student.id] === 'absent'
                                                            ? 'bg-red-500 text-white shadow-lg shadow-red-200'
                                                            : 'bg-light-bg text-light-text hover:bg-red-100/50'
                                                        }`}
                                                >
                                                    <X size={18} />
                                                </button>
                                                <button
                                                    onClick={() => toggleStatus(student.id, 'late')}
                                                    className={`px-3 py-1 flex items-center justify-center rounded-xl transition-all text-xs font-bold ${attendance[student.id] === 'late'
                                                            ? 'bg-orange-500 text-white shadow-lg shadow-orange-200'
                                                            : 'bg-light-bg text-light-text hover:bg-orange-100/50'
                                                        }`}
                                                >
                                                    LATE
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Attendance;
