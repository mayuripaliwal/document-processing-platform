import Sidebar from "./Sidebar";
import {Outlet} from "react-router-dom";

export default function DashboardLayout({setAuthStatus}){
    return (
        <div className="flex min-h-screen">
            <Sidebar setAuthStatus={setAuthStatus}/>
            <Outlet />
        </div>
    )
}