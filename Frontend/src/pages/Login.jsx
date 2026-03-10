import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn } from 'lucide-react';

const Login = () => {
    const navigate = useNavigate();

    const handleLogin = (e) => {
        e.preventDefault();
        // Simulate login
        navigate('/dashboard');
    };

    return (
        <div className="min-h-screen bg-light-bg flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-white rounded-3xl shadow-xl shadow-dark-primary/5 overflow-hidden border border-light-secondary/50">
                <div className="bg-dark-primary p-8 text-center text-white">
                    <div className="bg-dark-highlight w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 text-dark-primary">
                        <span className="text-3xl font-bold">TF</span>
                    </div>
                    <h2 className="text-2xl font-bold">Welcome Back</h2>
                    <p className="text-white/60 text-sm mt-2">Sign in to manage your classes</p>
                </div>

                <form onSubmit={handleLogin} className="p-8 space-y-6">
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-dark-primary pl-1">Email Address</label>
                        <input
                            type="email"
                            required
                            className="w-full px-4 py-3 rounded-xl border border-light-secondary focus:border-dark-accent focus:ring-2 focus:ring-dark-accent/20 outline-none transition-all placeholder:text-light-text/30"
                            placeholder="teacher@university.edu"
                        />
                    </div>

                    <div className="space-y-2">
                        <div className="flex justify-between items-center pl-1">
                            <label className="text-sm font-semibold text-dark-primary">Password</label>
                            <a href="#" className="text-xs text-dark-accent hover:underline">Forgot password?</a>
                        </div>
                        <input
                            type="password"
                            required
                            className="w-full px-4 py-3 rounded-xl border border-light-secondary focus:border-dark-accent focus:ring-2 focus:ring-dark-accent/20 outline-none transition-all"
                            placeholder="••••••••"
                        />
                    </div>

                    <div className="flex items-center gap-2 pl-1">
                        <input type="checkbox" id="remember" className="rounded border-light-secondary text-dark-primary focus:ring-dark-primary/20" />
                        <label htmlFor="remember" className="text-sm text-light-text">Remember me for 30 days</label>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-dark-primary text-white py-4 rounded-xl font-bold hover:bg-dark-secondary transition-all flex items-center justify-center gap-2 shadow-lg shadow-dark-primary/20"
                    >
                        <LogIn size={20} />
                        Sign In
                    </button>

                    <div className="relative py-2">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-light-secondary"></div>
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-white px-2 text-light-text/60">Or continue with</span>
                        </div>
                    </div>

                    <button
                        type="button"
                        className="w-full bg-white border border-light-secondary text-dark-primary py-4 rounded-xl font-semibold hover:bg-light-bg transition-all flex items-center justify-center gap-3"
                    >
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="w-5 h-5" />
                        Sign in with Google
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
