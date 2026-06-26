import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { handleLogin } from "../api/auth";

export default function Login() {
    const [username, setUsername] = useState("");
    const [pass, setPass] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    async function handleSubmit(e: React.SyntheticEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await handleLogin(username, pass);
            localStorage.setItem("access_token", data.access);
            localStorage.setItem("refresh_token", data.refresh);
            navigate("/dashboard");
        } catch (err) {
            alert("Login failed — check your credentials");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center px-4">
            <div className="w-full max-w-sm">

                {/* Signature element — ticker-style header */}
                <div className="mb-8 text-center">
                    <div className="font-mono text-[#00E08C] text-xs tracking-[0.3em] mb-2">
                        VECTORTRADE
                    </div>
                    <div className="h-px w-12 bg-[#00E08C] mx-auto mb-6" />
                    <h1 className="text-white text-2xl font-semibold">Sign in</h1>
                    <p className="text-[#6B6B7D] text-sm mt-1">Access your portfolio</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="username" className="block text-[#6B6B7D] text-xs font-mono mb-1.5 tracking-wide">
                            USERNAME
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="johndoe"
                            required
                            className="w-full bg-[#13131A] border border-[#232330] rounded-md px-4 py-2.5 text-white text-sm placeholder:text-[#3F3F4D] focus:outline-none focus:border-[#00E08C] transition-colors"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-[#6B6B7D] text-xs font-mono mb-1.5 tracking-wide">
                            PASSWORD
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={pass}
                            onChange={(e) => setPass(e.target.value)}
                            placeholder="••••••••"
                            required
                            className="w-full bg-[#13131A] border border-[#232330] rounded-md px-4 py-2.5 text-white text-sm placeholder:text-[#3F3F4D] focus:outline-none focus:border-[#00E08C] transition-colors"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-[#00E08C] text-[#04342C] font-medium text-sm py-2.5 rounded-md hover:bg-[#00C97D] transition-colors disabled:opacity-50 mt-2"
                    >
                        {loading ? "Signing in..." : "Sign in"}
                    </button>
                </form>

                <p className="text-center text-[#6B6B7D] text-sm mt-6">
                    No account?{" "}
                    <Link to="/register" className="text-[#00E08C] hover:underline">
                        Create one
                    </Link>
                </p>
            </div>
        </div>
    );
}
