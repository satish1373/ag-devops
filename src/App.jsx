import { useState, useEffect } from 'react';
import ExportToCSV from './components/ExportToCSV';

function App() {
  const [todos, setTodos] = useState([]);

  useEffect(() => {
    // Fetch todos from API or some other source
    // setTodos(fetchedTodos);
  }, []);

  return (
    <div className='App'>
      <h1>Todo Dashboard</h1>
      <ExportToCSV todos={todos} />
      {/* Rest of the app goes here */}
    </div>
  );
}

export default App;