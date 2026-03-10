import React from 'react';
import { Search, Filter, MoreVertical, Mail, Phone, Download } from 'lucide-react';

const StudentRow = ({ student }) => (
    <tr className="hover:bg-light-bg/50 transition-colors group">
        <td className="py-4 px-6">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-dark-secondary/10 flex items-center justify-center text-dark-primary font-bold text-sm">
                    {student.name.split(' ').map(n => n[0]).join('')}
                </div>
                <div>
                    <p className="text-sm font-bold text-dark-primary">{student.name}</p>
                    <p className="text-xs text-light-text">{student.email}</p>
                </div>
            </div>
        </td>
        <td className="py-4 px-6 text-sm font-medium text-dark-primary">{student.roll_number}</td>
        <td className="py-4 px-6 text-sm text-light-text">{student.course}</td>
        <td className="py-4 px-6">
            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${student.attendance >= 75 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                {student.attendance}%
            </div>
        </td>
        <td className="py-4 px-6 text-sm font-bold text-dark-primary">{student.cgpa}</td>
        <td className="py-4 px-6 text-right">
            <button className="p-2 text-light-text hover:bg-white hover:shadow-sm rounded-lg transition-all opacity-0 group-hover:opacity-100">
                <MoreVertical size={18} />
            </button>
        </td>
    </tr>
);

const Students = () => {
    const dummyStudents = [
        { id: 1, name: 'Alex Thompson', email: 'alex.t@edu.com', roll_number: '2022CS01', course: 'Data Structures', attendance: 88, cgpa: 3.8 },
        { id: 2, name: 'Emma Wilson', email: 'emma.w@edu.com', roll_number: '2022CS05', course: 'Data Structures', attendance: 72, cgpa: 3.2 },
        { id: 3, name: 'Jessica Chen', email: 'jess.c@edu.com', roll_number: '2022CS12', course: 'Data Structures', attendance: 95, cgpa: 3.9 },
        { id: 4, name: 'Ryan Miller', email: 'ryan.m@edu.com', roll_number: '2022CS08', course: 'Data Structures', attendance: 68, cgpa: 2.5 },
    ];

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Student Analytics</h1>
                    <p className="text-light-text mt-1">Detailed performance and engagement metrics.</p>
                </div>
                <div className="flex gap-3">
                    <button className="bg-white px-4 py-2 rounded-xl text-dark-primary font-semibold text-sm border border-light-secondary flex items-center gap-2 hover:bg-light-bg transition-all">
                        <Download size={18} />
                        Export CSV
                    </button>
                    <button className="bg-dark-primary text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-dark-secondary transition-all shadow-lg shadow-dark-primary/20">
                        Enrol Student
                    </button>
                </div>
            </div>

            <div className="bg-white rounded-3xl border border-light-secondary/50 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-light-secondary/50 flex flex-col sm:flex-row justify-between gap-4">
                    <div className="flex items-center gap-4 bg-light-bg px-4 py-2 rounded-xl flex-1 max-w-md">
                        <Search size={18} className="text-light-text/50" />
                        <input
                            type="text"
                            placeholder="Search by name, roll number..."
                            className="bg-transparent border-none outline-none text-sm w-full py-1"
                        />
                    </div>
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 border border-light-secondary rounded-xl text-sm font-semibold text-light-text hover:bg-light-bg transition-all">
                            <Filter size={18} />
                            Filter
                        </button>
                        <select className="px-4 py-2 border border-light-secondary rounded-xl text-sm font-semibold text-dark-primary outline-none cursor-pointer">
                            <option>All Courses</option>
                            <option>Data Structures</option>
                            <option>Algorithms</option>
                        </select>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-light-bg/30 text-[10px] uppercase tracking-widest font-bold text-light-text">
                            <tr>
                                <th className="py-4 px-6">Name</th>
                                <th className="py-4 px-6">Roll Number</th>
                                <th className="py-4 px-6">Primary Course</th>
                                <th className="py-4 px-6">Attendance</th>
                                <th className="py-4 px-6">CGPA</th>
                                <th className="py-4 px-6"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-light-secondary/30">
                            {dummyStudents.map(student => (
                                <StudentRow key={student.id} student={student} />
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="p-4 border-t border-light-secondary/50 bg-light-bg/10 flex justify-between items-center px-8">
                    <p className="text-xs text-light-text font-medium">Showing 4 of 245 students</p>
                    <div className="flex gap-2">
                        <button className="px-3 py-1 bg-white border border-light-secondary rounded-lg text-xs font-bold text-light-text hover:bg-light-bg transition-all disabled:opacity-50">Prev</button>
                        <button className="px-3 py-1 bg-dark-primary text-white rounded-lg text-xs font-bold hover:bg-dark-secondary transition-all">Next</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Students;
