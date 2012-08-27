Services-library and database.sql are the body of Services - services management environment.

Services have tree sections
- Database as core of services
- Clients like Renki and renkiadm
- Servers like Renkisrv

Getting started:
- create database named services to postgresql
- run sql/create_database.sh script
- create admin user account with group admins
- create normal user account with group users

- use admin user to create first customer 
 - customer number 0 is for your company

- create first domain with t_customers_id 0 and t_domain_id 0
- create user with t_domains_id = 0

- add some networks to t_subnets table
- add some addresses to t_addresses table using resently created subnets

- add services to t_services table (eg vhost servers)

Services is licensed under MIT-license

Copyright (c) 2012 Kapsi Internet-käyttäjät ry

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.