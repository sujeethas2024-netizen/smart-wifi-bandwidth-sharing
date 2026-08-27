import { useEffect, useState } from "react";
import { networkApi } from "../services/api";
import { generateUsers } from "../data/mockData";

export function useLiveUsers(pollMs = 3000) {
  const [users, setUsers] = useState(() => generateUsers());
  const [live, setLive] = useState(false);

  useEffect(() => {
    let stop = false;
    const pull = async () => {
      try {
        const res = await networkApi.users();
        if (!stop && res?.ok && Array.isArray(res.users) && res.users.length > 0) {
          setUsers(res.users);
          setLive(true);
        }
      } catch {
        // keep last known data when backend is unreachable
      }
    };
    pull();
    const id = setInterval(pull, pollMs);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [pollMs]);

  return { users, setUsers, live };
}
