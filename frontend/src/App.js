import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import React, { useState } from 'react';
import axios from 'axios';
import Form from 'react-bootstrap/Form';
import { Button } from 'react-bootstrap';
import { Graphviz } from 'graphviz-react';

function App() {
  const [address, setAddress] = useState('');
  const [graph, setGraph] = useState('graph {}')

  const getGraph = async (e) => {
    console.log("CLICKED!");
    const response = await axios.get(`http://localhost:5000/api/graph/${address}`)
    if (response.status != 200) {
      console.log("ERROR: %s", response.data);
    }

    setGraph(response.data)
  };

  return (
    <div className="App">
      <h1>AccessControl permissions visualization</h1>
      <Form.Group className="inputFields">
        <Form.Control type="text" id="address" placeholder="Contract Address" onChange={e => setAddress(e.target.value)} />
        <Button variant="primary" onClick={getGraph}>Get</Button>
      </Form.Group>
      <Graphviz dot={graph} />
    </div>
  );
}

export default App;
