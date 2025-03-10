workspace {
    name "Messanger"
    !identifiers hierarchical
    model {

        # External systems
        push = softwareSystem "Система отправки уведомлений" "Внешняя система для отправки push-уведомлений пользователям"

        # Internal system
        messanger = softwareSystem "Мессенджер" "Приложение для обмена сообщениями между пользователями и в групповых чатах" {
            -> push "Отправляет уведомления"
            db = container "Database" "Хранит данные пользователей, чатов и сообщений" {
                technology "PostgreSQL"
            }
            broker = container "Message Broker" "Обеспечивает асинхронный обмен сообщениями и хранение оффлайн-сообщений" {
                technology "RabbitMQ"
                -> push "Отправляет уведомления"
            }
            api = container "API Application" "Обрабатывает запросы от клиентов и реализует API" {
                technology "Django Rest Framework, Python"
                -> db "Читает и пишет данные" "JDBC"
                -> broker "Отправляет сообщения и уведомления"
                data_access = component "Data Access Layer" "Обеспечивает доступ к данным в базе данных" {
                    -> db "Пишет и читает данные"
                }
                auth = component "Authentication & Authorization" "Обеспечивает аутентификацию и авторизацию пользователей"{
                    -> data_access "Проверяет учетные данные"
                }
                user_management = component "User Management Controller" "Обрабатывает запросы, связанные с управлением пользователями (создание, поиск)" {
                    -> data_access "Использует"
                    -> auth "Выполняет аутентификацию"
                }
                chat_management = component "Chat Management Controller" "Обрабатывает запросы, связанные с управлением чатами (создание, добавление пользователей)" {
                    -> data_access "Использует"
                }
                message_management = component "Message Management Controller" "Обрабатывает запросы, связанные с отправкой и получением сообщений" {
                    -> data_access "Использует"
                    -> broker "Публикует сообщения в очередь"
                }
            }
            web = container "Web Application" "Пользовательский интерфейс для веб-клиента" {
                technology "Django, HTML, CSS, JavaScript"
                -> api "Использует API" "HTTPS"
            }
        }

        # Actors
        user = person "Пользователь мессенджера" "Отправляет и получает сообщения, создает чаты, управляет контактами"

        user -> messanger.web "Вводит информацию в форму"

        deploymentEnvironment "PROD" {
            deploymentNode "DMZ" {
                deploymentNode "web.messenger.com" {
                    containerInstance messanger.web
                }
            }

            deploymentNode "PROTECTED" {
                deploymentNode "k8s.namespace" {
                    lb = infrastructureNode "LoadBalancer"

                    pod1 = deploymentNode "pod1" {
                        api_instance = containerInstance messanger.api
                        instances 3
                    }

                    pod2 = deploymentNode "pod2" {
                        broker_instance = containerInstance messanger.broker
                    }

                    pod3 = deploymentNode "pod3" {
                        db_instance = containerInstance messanger.db
                    }

                    lb -> pod1.api_instance "Направляет запросы API"
                }
            }
        }

    }

    views {
        systemContext messanger {
            include *
            autoLayout
        }

        container messanger {
            include *
            autoLayout
        }

        component messanger.api {
            include *
            autoLayout
        }

        deployment * "PROD" {
            include *
            autoLayout

        }

        dynamic messanger alg_sent "Sent PtP message" {
            user -> messanger.web "Набирает сообщение в форму"
            messanger.web -> messanger.api "Отправляет сообщение" "HTTPS"
            messanger.api -> messanger.db "Сохраняет сообщение" "JDBC"
            messanger.api -> messanger.broker "Публикует сообщение в очередь"
            messanger.broker -> messanger.api "Обрабатывает очередь оффлайн-сообщений"
            messanger.api -> messanger.db "Обновляет статус сообщения" "JDBC"
            messanger.api -> messanger.broker "Отправляет уведомление"
            messanger.broker -> push "Отправляет push-уведомление"
            autoLayout
        }

        dynamic messanger alg_create "Create new user" {
            user -> messanger.web "Вводит данные о новом пользователе"
            messanger.web -> messanger.api "Запрашивает создание пользователя" "HTTPS"
            messanger.api -> messanger.db "Сохраняет пользователя в базе" "JDBC"
            autoLayout
        }

        dynamic messanger alg_add "Add user to chat" {
            user -> messanger.web "Вводит данные"
            messanger.web -> messanger.api "Запрашивает добавление пользователя в чат" "HTTPS"
            messanger.api -> messanger.db "Добавляет пользователя в чат и обновляет данные" "JDBC"
            autoLayout
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Person" {
                background #08427b
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85BBDD
                color #ffffff
            }
        }
    }
}
