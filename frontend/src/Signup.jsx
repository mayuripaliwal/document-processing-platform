import {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';

export default function Signup() {
    const BACKEND_URL=import.meta.env.VITE_BACKEND_URL;

    const [userEmail, setUserEmail]=useState("");
    const [userPassword, setUserPassword]=useState("");

    const [errorMessage, setErrorMessage]=useState("");
    const navigate=useNavigate();

    const [loading, setLoading]=useState(false);

    async function handleSignup(event){
        event.preventDefault();
        setErrorMessage("");
        setLoading(true);
        const payload={
            "email":userEmail, 
            "password":userPassword
        }
        try{
            const response = await fetch(`${BACKEND_URL}/signup`,{
                method:"POST",
                credentials:"include",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify(payload)
            });

            if (!response.ok){
                {/**Account already exists */}
                if (response.status===409){
                    setErrorMessage("Account already exists.");
                }
                else if (response.status===422){
                    setErrorMessage("Invalid input fields.")
                }
                else {
                    setErrorMessage("Something went wrong. Please try again.")
                }
            }
            else{
                {/**Sign up successful */}
                navigate("/login");
            }
        }
        catch(error){
            setErrorMessage("Unable to connect to the server. Please try again.")
        }
        finally{
            setLoading(false);
        }
    }
  return (
    <>
      <div className="flex min-h-full flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <h2 className="mt-6 text-center text-2xl/9 font-bold tracking-tight text-gray-900">
            Create your account
          </h2>
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-[480px]">
          <div className="bg-white px-6 py-12 shadow-sm sm:rounded-lg sm:px-12">
            <form onSubmit={handleSignup} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm/6 font-medium text-gray-900">
                  Email address
                </label>
                <div className="mt-2">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    onChange={(e)=>setUserEmail(e.target.value)}
                    autoComplete="email"
                    className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm/6 font-medium text-gray-900">
                  Password
                </label>
                <div className="mt-2">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    minLength="8"
                    required
                    onChange={(e)=>setUserPassword(e.target.value)}
                    autoComplete="current-password"
                    className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-xs hover:bg-indigo-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                >
                  {loading? "Signing up..." : "Sign up"}
                </button>
              </div>
              {errorMessage && (
                <p className="text-center text-red-600">
                    {errorMessage}
                </p>
                )
              }
            </form>
          </div>

          <p className="mt-10 text-center text-sm/6 text-gray-500">
            Already a member?{' '}
            <Link 
            to="/signin"
            className="font-semibold text-indigo-600 hover:text-indigo-500">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  )
}
