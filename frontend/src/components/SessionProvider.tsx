"use client";

import { navigateToFreshSession } from "@/lib/session-navigation";

import { createContext, useContext } from "react";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
export type Identity = {id:string; username:string; role:"admin"|"dosen"|"penjamin_mutu"};
const Session = createContext<Identity | null>(null);
export const useIdentity = () => useContext(Session);
export function SessionProvider({user,children}:{user:Identity;children:React.ReactNode}) { return <Session.Provider value={user}>{children}</Session.Provider>; }
export function SessionMenu() {
  const user=useIdentity();
  return <div className="flex items-center gap-3 text-sm"><span>{user?.username} · {user?.role.replaceAll("_"," ")}</span><Button variant="outline" size="sm" onClick={async()=>{try {await apiFetch("/api/auth/logout",{method:"POST"});navigateToFreshSession("/login");}catch(e){alert((e as Error).message);}}}>Keluar</Button></div>;
}
