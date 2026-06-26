import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { handleRegister } from "../api/auth";

export default function Register() {
    const [fn, setFN] = useState("");
    const [ln, setLN] = useState("");
    const [email, setEmail] = useState("");
    const [user, setUser] = useState("");
    const [pass, setPass] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    async function handleSubmit(e: React.SyntheticEvent) {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await handleRegister(fn, ln, email, user, pass);
            localStorage.setItem("access_token", data.access);
            localStorage.setItem("refresh_token", data.refresh);
            navigate("/dashboard");
        } catch (err) {
            alert("Registration failed — try a different username");
        } finally {
            setLoading(false);
        }
    }

    const inputClass =
        "w-full bg-[#13131A] border border-[#232330] rounded-md px-4 py-2.5 text-white text-sm placeholder:text-[#3F3F4D] focus:outline-none focus:border-[#00E08C] transition-colors";
    const labelClass = "block text-[#6B6B7D] text-xs font-mono mb-1.5 tracking-wide";

    return (
        <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center px-4 py-12">
            <div className="w-full max-w-sm">

                <div className="mb-8 text-center">
                    <div className="font-mono text-[#00E08C] text-xs tracking-[0.3em] mb-2">
                        VECTORTRADE
                    </div>
                    <div className="h-px w-12 bg-[#00E08C] mx-auto mb-6" />
                    <h1 className="text-white text-2xl font-semibold">Create account</h1>
                    <p className="text-[#6B6B7D] text-sm mt-1">Start with $100,000 in simulated cash</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label htmlFor="first_name" className={labelClass}>FIRST NAME</label>
                            <input id="first_name" type="text" value={fn} onChange={(e) => setFN(e.target.value)} placeholder="John" required className={inputClass} />
                        </div>
                        <div>
                            <label htmlFor="last_name" className={labelClass}>LAST NAME</label>
                            <input id="last_name" type="text" value={ln} onChange={(e) => setLN(e.target.value)} placeholder="Doe" required className={inputClass} />
                        </div>
                    </div>

                    <div>
                        <label htmlFor="email" className={labelClass}>EMAIL</label>
                        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="john@example.com" required className={inputClass} />
                    </div>

                    <div>
                        <label htmlFor="username" className={labelClass}>USERNAME</label>
                        <input id="username" type="text" value={user} onChange={(e) => setUser(e.target.value)} placeholder="johndoe" required className={inputClass} />
                    </div>

                    <div>
                        <label htmlFor="password" className={labelClass}>PASSWORD</label>
                        <input id="password" type="password" value={pass} onChange={(e) => setPass(e.target.value)} placeholder="••••••••" required className={inputClass} />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-[#00E08C] text-[#04342C] font-medium text-sm py-2.5 rounded-md hover:bg-[#00C97D] transition-colors disabled:opacity-50 mt-2"
                    >
                        {loading ? "Creating account..." : "Create account"}
                    </button>
                </form>

                <p className="text-center text-[#6B6B7D] text-sm mt-6">
                    Already have an account?{" "}
                    <Link to="/login" className="text-[#00E08C] hover:underline">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
}
