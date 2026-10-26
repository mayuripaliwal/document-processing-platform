import { useState, useEffect } from 'react'
import './App.css'
import LandingPage from "./LandingPage";
import Signup from "./Signup";
import Signin from "./Signin";
import Dashboard from "./Dashboard";
import Documents from "./Documents";
import DashboardLayout from "./DashboardLayout";
import {BrowserRouter, Routes, Route, Link} from "react-router-dom";
import {AUTH_STATUSES} from "./AuthConfig";

function App() {
  const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;
  const [authStatus, setAuthStatus]=useState(AUTH_STATUSES.CHECKING);
  async function getAuthStatus(){
    setAuthStatus(AUTH_STATUSES.CHECKING);
    try{
      const response = await fetch(`${BACKEND_URL}/auth`,{
        method:"GET",
        credentials:"include",
        headers:{
          "Content-Type":"application/json"
        }
      });

      if (!response.ok){
        setAuthStatus(AUTH_STATUSES.LOGGED_OUT);
      }
      else{
        setAuthStatus(AUTH_STATUSES.LOGGED_IN);
      }
    }
    catch(e){
      console.log(e);
      setAuthStatus(AUTH_STATUSES.LOGGED_OUT);
    }
  }

  useEffect(()=>{
    getAuthStatus()
  },[])
  return (
    
    <>
    <BrowserRouter>
    
    {authStatus === AUTH_STATUSES.CHECKING && ( 
      <div>
        <p
        className="mt-4 text-center text-gray-900 text-xl"
        >Checking authentication...</p>;
      </div>
      )
    }
    <Routes>
      {authStatus === AUTH_STATUSES.LOGGED_IN && (
        <>
        <Route element={<DashboardLayout setAuthStatus={setAuthStatus}/>}>
          <Route path="/dashboard" element={<Dashboard setAuthStatus={setAuthStatus}/>}></Route>
          <Route path="/documents" element={<Documents setAuthStatus={setAuthStatus}/>}></Route>
        </Route>
        <Route path="/*" element={<Dashboard setAuthStatus={setAuthStatus}/>}></Route>
        </>
      )}
      {authStatus === AUTH_STATUSES.LOGGED_OUT && (
        <>
        <Route path="/" element={<LandingPage/>}></Route>
        <Route path="/signup" element={<Signup/>}></Route>
        <Route path="/signin" element={<Signin setAuthStatus={setAuthStatus}/>}></Route>
        <Route path="/*" element={<Signin setAuthStatus={setAuthStatus}/>}></Route>
        </>
      )
    }
    </Routes>
    </BrowserRouter>
    </>
  )
}

export default App
