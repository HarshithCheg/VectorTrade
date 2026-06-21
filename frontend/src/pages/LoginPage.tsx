import { useState } from "react";
import { handleLogin } from "../api/auth";
import { useNavigate } from "react-router-dom";


export default function Login(){
    const [username, setUsername] = useState("");
    const [pass, setPass] = useState("");
    const navigate = useNavigate();

    async function handleSubmit(e:React.FormEvent){
        e.preventDefault();
        try{
            const data = await handleLogin(username, pass)
            localStorage.setItem("access_token", data.access)
            localStorage.setItem('refresh_token', data.refresh)
            navigate('pages/dashboard');
        } catch(e){
            Error("Login : Failed")
        }
    }

    return( 
        <>
            <div>LOGIN
                <form onSubmit={handleSubmit}>
                    <label htmlFor='username'> USERNAME: </label>
                    <input type="text" id="username" name="username" placeholder="JohnDoe"  value={username} onChange={(e) => setUsername(e.target.value)} required/>

                    <label htmlFor='password'> PASSWORD: </label>
                    <input type="password" id="password" name="password" value={pass} onChange={(e) => setPass(e.target.value)} required/>    
                    <button type='submit'>LOGIN</button>         
                </form>
            </div>
        </>
    )
}