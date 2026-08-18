let userCount = 0;

let allocationChart = null;


// ----------------------------------
// Add User
// ----------------------------------

function addUser() {

    userCount++;

    const container =
        document.getElementById("users");


    const row =
        document.createElement("div");


    row.className =
        "user-row";


    row.id =
        `user-${userCount}`;


    row.innerHTML = `

        <input
            type="text"
            class="form-control username"
            placeholder="User ${userCount}"
        >


        <select
            class="form-control activity"
        >

            <option value="browsing">
                Browsing
            </option>

            <option value="online_class">
                Online Class
            </option>

            <option value="gaming">
                Gaming
            </option>

            <option value="streaming">
                Streaming
            </option>

            <option value="downloading">
                Downloading
            </option>

        </select>


        <input
            type="number"
            class="form-control bandwidth"
            value="10"
            min="1"
        >


        <button
            class="btn btn-danger"
            onclick="removeUser(${userCount})"
        >

            Remove

        </button>

    `;


    container.appendChild(row);
}


// ----------------------------------
// Remove User
// ----------------------------------

function removeUser(id) {

    const row =
        document.getElementById(
            `user-${id}`
        );


    if (row) {

        row.remove();

    }
}


// ----------------------------------
// Calculate Allocation
// ----------------------------------

async function calculateAllocation() {

    const totalBandwidth =
        parseFloat(
            document.getElementById(
                "totalBandwidth"
            ).value
        );


    const rows =
        document.querySelectorAll(
            ".user-row"
        );


    const users = [];


    rows.forEach(
        (row, index) => {

            const activity =
                row.querySelector(
                    ".activity"
                ).value;


            const bandwidth =
                parseFloat(
                    row.querySelector(
                        ".bandwidth"
                    ).value
                );


            users.push({

                user_id:
                    index + 1,

                activity:
                    activity,

                requested_bandwidth:
                    bandwidth

            });

        }
    );


    if (users.length === 0) {

        alert(
            "Please add at least one user."
        );

        return;
    }


    try {

        const response =
            await fetch(
                "/api/allocate",
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            total_bandwidth:
                                totalBandwidth,

                            users:
                                users

                        })

                }
            );


        const result =
            await response.json();


        if (
            result.status !==
            "success"
        ) {

            alert(
                result.message
            );

            return;
        }


        displayResults(
            result.data
        );


    }
    catch (error) {

        console.error(error);

        alert(
            "Unable to connect to server."
        );

    }
}


// ----------------------------------
// Display Results
// ----------------------------------

function displayResults(data) {

    const container =
        document.getElementById(
            "resultContent"
        );


    let html = `

        <div class="row">

            <div class="col-md-4">

                <div class="result-box">

                    <p>
                        Total Bandwidth
                    </p>

                    <div class="metric">
                        ${data.total_bandwidth}
                        Mbps
                    </div>

                </div>

            </div>


            <div class="col-md-4">

                <div class="result-box">

                    <p>
                        Jain Fairness Index
                    </p>

                    <div class="metric">
                        ${data.fairness_index}
                    </div>

                </div>

            </div>


            <div class="col-md-4">

                <div class="result-box">

                    <p>
                        Iterations
                    </p>

                    <div class="metric">
                        ${data.iterations}
                    </div>

                </div>

            </div>

        </div>


        <hr>

        <h4>
            User Allocation
        </h4>

        <div class="table-responsive">

        <table class="table">

            <thead>

                <tr>

                    <th>User</th>

                    <th>Activity</th>

                    <th>Requested</th>

                    <th>Allocated</th>

                    <th>Utility</th>

                </tr>

            </thead>

            <tbody>
    `;


    data.users.forEach(
        user => {

            html += `

                <tr>

                    <td>
                        User ${user.user_id}
                    </td>

                    <td>
                        ${user.activity}
                    </td>

                    <td>
                        ${user.requested_bandwidth}
                        Mbps
                    </td>

                    <td>
                        <strong>
                            ${user.allocated_bandwidth}
                            Mbps
                        </strong>
                    </td>

                    <td>
                        ${user.utility}
                    </td>

                </tr>

            `;

        }
    );


    html += `

            </tbody>

        </table>

        </div>
    `;


    container.innerHTML =
        html;


    drawChart(data);
}


// ----------------------------------
// Chart
// ----------------------------------

function drawChart(data) {

    const labels =
        data.users.map(
            user =>
                `User ${user.user_id}`
        );


    const values =
        data.users.map(
            user =>
                user.allocated_bandwidth
        );


    const ctx =
        document.getElementById(
            "allocationChart"
        );


    if (allocationChart) {

        allocationChart.destroy();

    }


    allocationChart =
        new Chart(
            ctx,
            {

                type: "bar",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Allocated Bandwidth (Mbps)",

                            data:
                                values

                        }

                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }
        );
}


// ----------------------------------
// Start with 3 users
// ----------------------------------

addUser();

addUser();

addUser();