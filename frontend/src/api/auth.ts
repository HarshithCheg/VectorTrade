import { BASE_URL } from '../../constants'
import type { AuthResponse } from '../types/index';

export async function handleLogin(username:string, password:string): Promise<AuthResponse> {
    const response = await fetch(`${BASE_URL}/api/login/`,{
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password}),
    });
    const data = await response.json();
    if(!response.ok){
        throw new Error(`${data.username} login: fail`);
    }
    return data;
}

export async function handleRegister(first_name: string, last_name:string, email:string, username:string, password:string): Promise<AuthResponse>{
    const response = await fetch(`${BASE_URL}/api/register/`,{
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({first_name, last_name, email, username, password})
    });
    const data = await response.json();
    if(!response.ok){
        throw new Error(`${data.username} register: fail`);
    }
    return data;
}